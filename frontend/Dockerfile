FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . /app

EXPOSE 3000

# Start Vite dev server exposing all network hosts
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
