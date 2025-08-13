FROM node:bookworm-slim

WORKDIR /app

# Copy package files first (better Docker caching)
COPY package*.json ./

# Install dependencies first
RUN npm install

# Then copy the rest of the application
COPY . .

# Run the application
CMD ["npm", "start"]