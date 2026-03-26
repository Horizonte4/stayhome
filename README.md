# 🏠 StayHome

Plataforma de alquiler de alojamientos desarrollada con **Django** y **PostgreSQL**, containerizada con **Docker**.

---

## 📋 Requisitos previos

Asegúrate de tener instalado lo siguiente antes de comenzar:

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/Horizonte4/stayhome.git
cd stayhome
```

### 2. Construir y levantar los contenedores

```bash
docker compose up --build
```

Esto levantará dos servicios:
- **web** — aplicación Django
- **db** — base de datos PostgreSQL

### 3. Aplicar las migraciones

En una terminal aparte (con los contenedores corriendo):

```bash
docker compose exec web python manage.py migrate
```

### 4. Crear un superusuario (opcional)

```bash
docker compose exec web python manage.py createsuperuser
```

### 5. Acceder a la aplicación

Abre tu navegador en:

```
http://localhost:8000
```

Panel de administración:

```
http://localhost:8000/admin
```

---

##  Detener los contenedores

```bash
docker compose down
```
---

## 👥 Equipo de desarrollo

| Nombre | GitHub | Rol |
|---|---|---|
| Jerónimo Gómez | [@Horizonte4](https://github.com/Horizonte4) | Developer |
| Laura Marín | [@lauramarin15](https://github.com/lauramarin15) | Developer |
| Mateo Cadavid | [@Mcadavidr2](https://github.com/Mcadavidr2) | Developer |

---

## Tecnologías utilizadas

- [Django](https://www.djangoproject.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
