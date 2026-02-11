FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port Vite default
EXPOSE 5173

# Start Dev Server
CMD ["npm", "run", "dev", "--", "--host"]