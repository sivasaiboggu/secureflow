"""SDK-shaped page fixtures only. No AWS endpoint is contacted."""
import unittest
from unittest.mock import Mock, patch
from app.scanners.pagination import aws_items
from app.scanners.base import ScanUnavailable
from app.scanners.aws.s3 import S3Scanner
from app.scanners.aws.ec2 import EC2Scanner
from app.scanners.aws.iam import IAMScanner
from app.scanners.aws.rds_scanner import RDSScanner
from app.scanners.aws.lambda_scanner import LambdaScanner
from app.scanners.aws.vpc_scanner import VPCScanner

CREDS={'aws_access_key_id':'synthetic-key','aws_secret_access_key':'synthetic-secret'}

class PaginationTests(unittest.TestCase):
    def test_token_contracts_and_filters(self):
        for request,response,truncated in [('NextToken','NextToken',None),('Marker','Marker',None),('Marker','NextMarker',None),('ContinuationToken','ContinuationToken',None),('Marker','Marker','IsTruncated')]:
            with self.subTest(request=request,response=response,truncated=truncated):
                client=Mock();first={'Items':[{'id':1}],response:'page-two'}
                second={'Items':[{'id':2}]}
                if truncated:first[truncated]=True;second[truncated]=False
                client.list_items.side_effect=[first,second]
                rows=list(aws_items(client,'list_items','Items',request_token=request,response_token=response,truncated_key=truncated,UserName='synthetic'))
                self.assertEqual(rows,[{'id':1},{'id':2}])
                self.assertEqual(client.list_items.call_args_list[1].kwargs,{'UserName':'synthetic',request:'page-two'})
    def test_repeated_missing_tokens_and_bound_fail(self):
        client=Mock();client.list_items.return_value={'Items':[],'NextToken':'same'}
        with self.assertRaises(ScanUnavailable):list(aws_items(client,'list_items','Items'))
        client.list_items.return_value={'Items':[],'IsTruncated':True}
        with self.assertRaises(ScanUnavailable):list(aws_items(client,'list_items','Items',truncated_key='IsTruncated'))
        client.list_items.return_value={'Items':[],'NextToken':'next'}
        with self.assertRaises(ScanUnavailable):list(aws_items(client,'list_items','Items',max_pages=1))
    def test_late_provider_failure_clears_partial_scanner_findings(self):
        with patch('boto3.Session') as session:
            client=session.return_value.client.return_value
            client.list_buckets.side_effect=[{'Buckets':[{'Name':'one'}],'ContinuationToken':'more'},RuntimeError('private provider text')]
            scanner=S3Scanner('org','account',CREDS);scanner._scan_bucket=Mock(return_value=[{'id':'partial'}])
            with self.assertRaises(ScanUnavailable):scanner.scan()
            self.assertEqual(scanner.findings,[])
    def test_resource_scanners_visit_second_page(self):
        configs=[(S3Scanner,'list_buckets','Buckets','ContinuationToken','_scan_bucket',{'Name':'synthetic'}),
                 (EC2Scanner,'describe_instances','Reservations','NextToken','_scan_instance',{'Instances':[{'InstanceId':'synthetic'}]}),
                 (RDSScanner,'describe_db_instances','DBInstances','Marker','_scan_db_instance',{'DBInstanceIdentifier':'synthetic'}),
                 (LambdaScanner,'list_functions','Functions','NextMarker','_scan_function',{'FunctionName':'synthetic'}),
                 (VPCScanner,'describe_vpcs','Vpcs','NextToken','_scan_vpc',{'VpcId':'synthetic'}),
                 (IAMScanner,'list_users','Users','Marker','_scan_user',{'UserName':'synthetic'})]
        for cls,operation,key,token,method,item in configs:
            with self.subTest(scanner=cls.__name__),patch('boto3.Session') as session:
                client=session.return_value.client.return_value
                first={key:[],token:'more'};second={key:[item]}
                if cls is IAMScanner:first['IsTruncated']=True;second['IsTruncated']=False
                getattr(client,operation).side_effect=[first,second]
                scanner=cls('org','account',CREDS);setattr(scanner,method,Mock(return_value=[]))
                if cls is IAMScanner:scanner._check_account_password_policy=Mock(return_value=[])
                scanner.scan();getattr(scanner,method).assert_called_once()
                self.assertEqual(getattr(client,operation).call_count,2)

    def test_iam_nested_lists_visit_all_pages(self):
        with patch('boto3.Session') as session:
            client=session.return_value.client.return_value
            client.list_mfa_devices.side_effect=[{'MFADevices':[],'IsTruncated':True,'Marker':'mfa-next'},{'MFADevices':[{'SerialNumber':'synthetic'}],'IsTruncated':False}]
            client.list_access_keys.side_effect=[{'AccessKeyMetadata':[],'IsTruncated':True,'Marker':'keys-next'},{'AccessKeyMetadata':[],'IsTruncated':False}]
            scanner=IAMScanner('org','account',CREDS)
            self.assertEqual(scanner._scan_user('synthetic-user'),[])
            self.assertEqual(client.list_mfa_devices.call_args.kwargs,{'UserName':'synthetic-user','Marker':'mfa-next'})
            self.assertEqual(client.list_access_keys.call_args.kwargs,{'UserName':'synthetic-user','Marker':'keys-next'})

    def test_vpc_flow_logs_second_page_prevents_false_missing_log_finding(self):
        with patch('boto3.Session') as session:
            client=session.return_value.client.return_value
            client.describe_flow_logs.side_effect=[{'FlowLogs':[],'NextToken':'more'},{'FlowLogs':[{'FlowLogId':'synthetic'}]}]
            scanner=VPCScanner('org','account',CREDS)
            self.assertEqual(scanner._scan_vpc({'VpcId':'vpc-synthetic','IsDefault':False}),[])
            self.assertEqual(client.describe_flow_logs.call_args.kwargs,{'Filter':[{'Name':'resource-id','Values':['vpc-synthetic']}],'NextToken':'more'})

    def test_botocore_stubber_verifies_real_sdk_token_parameters_without_network(self):
        import boto3
        from botocore.stub import Stubber
        client=boto3.client('lambda',region_name='us-east-1',aws_access_key_id='synthetic',aws_secret_access_key='synthetic')
        with Stubber(client) as stub:
            stub.add_response('list_functions',{'Functions':[],'NextMarker':'more'}, {})
            stub.add_response('list_functions',{'Functions':[]}, {'Marker':'more'})
            self.assertEqual(list(aws_items(client,'list_functions','Functions',request_token='Marker',response_token='NextMarker')),[])
            stub.assert_no_pending_responses()
