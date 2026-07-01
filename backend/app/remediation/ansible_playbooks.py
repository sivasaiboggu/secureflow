import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AnsibleRemediationGenerator:
    """Generates Ansible Playbooks to fix host configuration and SSH access parameters"""
    
    def generate_ssh_hardening_playbook(self, host_group: str = "webservers") -> str:
        return f'''---
- name: Harden SSH Configurations and Disable Root Logins
  hosts: {host_group}
  become: yes
  tasks:
    - name: Disable Root Login over SSH
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^PermitRootLogin'
        line: 'PermitRootLogin no'
        state: present
      notify: Restart SSH Service

    - name: Enforce SSH protocol version 2
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^Protocol'
        line: 'Protocol 2'
        state: present
      notify: Restart SSH Service

  handlers:
    - name: Restart SSH Service
      service:
        name: sshd
        state: restarted
'''

    def generate_update_packages_playbook(self, host_group: str = "all") -> str:
        return f'''---
- name: Security Update System Package Dependencies
  hosts: {host_group}
  become: yes
  tasks:
    - name: Run apt-get update and upgrade security patches
      apt:
        upgrade: dist
        update_cache: yes
      when: ansible_os_family == "Debian"

    - name: Run yum security updates
      yum:
        name: '*'
        state: latest
        security: yes
      when: ansible_os_family == "RedHat"
'''

    def get_playbook(self, vuln_type: str, host_group: str = "all") -> str:
        vtype = vuln_type.upper()
        if "SSH" in vtype or "ROOT_LOGIN" in vtype:
            return self.generate_ssh_hardening_playbook(host_group)
        return self.generate_update_packages_playbook(host_group)

ansible_generator = AnsibleRemediationGenerator()
