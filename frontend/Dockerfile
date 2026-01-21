# Usa Node en lugar de Python
FROM node:20-alpine
WORKDIR /app

# Copia archivos de dependencias de Javascript
COPY package*.json ./

RUN npm install

# Copia el resto del código
COPY . .

EXPOSE 5173

# Comando para iniciar React (ajusta si usas Vite o CRA)
CMD ["npm", "run", "dev", "--", "--host"]

