FROM node:bookworm-slim

WORKDIR /app


# Install dependencies
COPY . .

RUN npm install

# Run the application
CMD ["npm", "start"]