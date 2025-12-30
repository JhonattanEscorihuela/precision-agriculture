# Usamos una imagen base de Node.js (ligera para producción y desarrollo)
FROM node:20-alpine

# Creamos un directorio para la aplicación dentro del contenedor
WORKDIR /app

# Copiamos los archivos necesarios para instalar las dependencias
COPY package.json yarn.lock ./

# Instalamos las dependencias
RUN yarn install

# Copiamos el resto del código fuente al contenedor
COPY . .

# Exponemos el puerto que usa Next.js por defecto
EXPOSE 3000

# Indicamos el comando para iniciar el servidor de desarrollo
CMD ["yarn", "dev"]