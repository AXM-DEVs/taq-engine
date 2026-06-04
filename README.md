# TaQ Engine — Tactical Analysis & Qualification Engine

[![Version](https://img.shields.io/badge/version-1.0.5-6c5ce7?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/python-3.12-3776AB?style=for-the-badge&logo=python)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi)]()
[![License](https://img.shields.io/badge/license-MIT-a29bfe?style=for-the-badge)]()

**desarrollado por [AXM](https://github.com/AXM-DEVs)**

---

## 🚀 ¿Qué es TaQ Engine?

TaQ Engine es un motor de inteligencia y automatización para plataformas OSINT (Open Source Intelligence). Proporciona:

- **Orquestación de investigaciones** mediante playbooks flexibles
- **Scoring multi-factor de amenazas** (freshness, source, correlation, reputación)
- **Consultas en lenguaje natural** → SQL/Cypher
- **Sistema de conectores** para integrar plataformas externas
- **REST API completa** con autenticación, rate limiting y control de acceso por tiers
- **Interfaz web** para gestión de investigaciones y playbooks

Pensado como núcleo extensible: cualquier plataforma externa (SENTINEL, MISP, Shodan, VirusTotal, etc.) puede conectarse mediante el sistema de conectores.

---

## ⭐ Características Principales

### 🔐 Seguridad y Autenticación
- Registro y login de usuarios con email/contraseña
- Hash de contraseñas seguro usando **bcrypt**
- Tokens de acceso JWT con expiración configurable
- Rate limiting por IP para prevenir ataques de fuerza bruta
- Endpoints protegidos con autenticación obligatoria (salud y documentación son públicos)

### 📊 Control de Acceso por Tiers (Free/Premium)
Todos los usuarios comienzan en el nivel **FREE** por defecto. Los límites se aplican dinámicamente:

| Característica | Plan FREE | Plan PREMIUM |
|----------------|-----------|--------------|
| Investigaciones por día | 10 | 1,000 |
| Conectores por investigación | 3 | 50 |
| Pasos máximos por playbook | 5 | 100 |
| Scorings por día | 50 | 10,000 |
| Consultas por día | 100 | 10,000 |
| Máximo playbooks por usuario | 5 | 100 |
| Acceso a conectores premium | ❌ No | ✅ Sí |
| Acceso a funciones premium (ej. reporte de abuse) | ❌ No | ✅ Sí |

> 💡 **Nota para auto-hosting**: En deployments auto-hospedados, los administradores pueden modificar manualmente el campo `tier` en la base de datos para asignar privilegios premium. En un servicio SaaS gestionado, este campo se actualiza automáticamente mediante el sistema de pagos.

### 🔧 Arquitectura y Escalabilidad
- **FastAPI** para alto rendimiento async
- **SQLAlchemy** con soporte para SQLite (dev) y PostgreSQL (prod)
- Diseño stateless para escalamiento horizontal detrás de load balancer
- Sistema de plugins para conectores (añade nuevas integraciones fácilmente)
- Caching configurable para mejor rendimiento

### 📱 Interfaz de Usuario
- **Landing page**: Información del producto y login
- **Dashboard**: Gestión de investigaciones, playbooks y estadísticas
- **System view**: Panel de administración (funcionalidad básica incluida)

### 📦 Sistema de Conectores
Integra fácilmente plataformas externas mediante el sistema de conectores. Incluidos de ejemplo:
- AbuseIPDB (free tier)
- Shodan (free tier)
- VirusTotal (free tier)
- DNS Resolver
- GeoIP local
- WHOIS lookup

---

## 🚀 Cómo Empezar en 3 Pasos Fáciles

¿No tienes experiencia con líneas de comando? ¡No te preocupes! Tenemos opciones para todos los niveles.

### 🖱️ Opción Fácil: Interfaz Gráfica (Recomendado para Principiantes)
1. **Descarga**: Haz clic en el botón verde **"Code"** arriba y selecciona **"Download ZIP"**
2. **Extrae**: Descomprime el archivo ZIP en una carpeta fácil de encontrar (como tu Escritorio)
3. **Ejecuta**: 
   - En Windows: Haz doble clic en el archivo `start-windows.bat`
   - En Mac/Linux: Haz doble clic en `start-mac-linux.sh` (o ejecútalo desde Terminal)
4. **¡Listo!**: Espera a que aparezca "Servidor iniciado" y abre tu navegador en:
   - 🌐 **Página de inicio**: http://localhost:8000
   - 📊 **Panel de control**: http://localhost:8000/dashboard
   - 📚 **Documentación API**: http://localhost:8000/docs

> 💡 **Primer uso**: Regístrate con tu email y contraseña en la página de inicio para comenzar a usar todas las funciones gratuitas.

### 💻 Opción Para Desarrolladores (Con Terminal)
Si te sientes cómodo con la terminal, estos son los comandos estándar:

```bash
# Obtener el código
git clone https://github.com/AXM-DEVs/taq-engine.git
cd taq-engine

# Preparar entorno (una sola vez)
pip install -r requirements.txt

# Iniciar servidor (con recarga automática durante desarrollo)
python -m taq.main --host 0.0.0.0 --port 8000 --reload

# Visitar: http://localhost:8000
```

### 🐳 Opción Docker (Para Equipos y Producción)
Ideal para equipos que quieren consistencia entre ambientes:

```bash
# Obtener el código
git clone https://github.com/AXM-DEVs/taq-engine.git
cd taq-engine

# Configurar (solo la primera vez)
cp .env.example .env
# Edita .env y pone una clave secreta: TAQ_SECRET_KEY=tu-clave-super-secreta-aqui

# Iniciar todo con un comando
docker-compose -f docker-compose.production.yml up -d

# Acceder a través de tu navegador:
# - http://localhost (interfaz web)
# - http://localhost/docs (documentación API)
```

### 🔑 Tu Primer Registro (30 segundos)
Una vez que el servidor esté corriendo:
1. Ve a http://localhost:8000
2. Haz clic en "Registrarse"
3. Ingresa tu email y una contraseña (mínimo 8 caracteres)
4. ¡Listo! Ya puedes comenzar a crear investigaciones

### 📱 ¿Qué Verás en tu Navegador?
- **Página de inicio**: Información sobre TaQ Engine y formulario de login/registro
- **Dashboard**: Vista gráfica de tus investigaciones, estadísticas y botón para crear nuevas
- **Panel de sistema**: Herramientas básicas de administración (útil para avancidados)

> 🌟 **Tip**: La primera vez que inicies el servidor, tardará unos segundos en preparar la base de datos. ¡Es normal! Busca el mensaje "Aplicación lista" en la terminal o en los logs de Docker.

---

## ⚙️ Configuración

TaQ Engine se configura mediante variables de entorno. Copia `.env.example` a `.env` y ajusta los valores según tu entorno.

### Variables de Entorno Esenciales

| Variable | Valor por Defecto | Descripción | Requerido en Producción |
|----------|------------------|-------------|-------------------------|
| `TAQ_DEBUG` | `false` | Activa modo debug (más logs) | `false` |
| `TAQ_SECRET_KEY` | `change-me` | Key secreta para JWT (¡CAMBIAR EN PRODUCCIÓN!) | ✅ Sí |
| `TAQ_DATA_DIR` | `./data` | Directorio para almacenamiento de datos | No |
| `TAQ_DB_ENGINE` | `sqlite` | Motor de base de datos (`sqlite` o `postgresql`) | No |
| `TAQ_DB_HOST` | `localhost` | Host de la base de datos | Sí (si no es sqlite) |
| `TAQ_DB_PORT` | `5432` | Puerto de la base de datos | Sí (si no es sqlite) |
| `TAQ_DB_USER` | `taq` | Usuario de la base de datos | Sí (si no es sqlite) |
| `TAQ_DB_PASSWORD` | `taq` | Contraseña de la base de datos | Sí (si no es sqlite) |
| `TAQ_DB_NAME` | `taq` | Nombre de la base de datos | Sí |
| `TAQ_LOG_LEVEL` | `INFO` | Nivel de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | No |
| `TAQ_CACHE_ENABLED` | `true` | Habilitar caching | No |
| `TAQ_CACHE_TTL` | `300` | TTL por defecto del caché en segundos | No |

> ⚠️ **Importante**: Nunca uses el valor por defecto de `TAQ_SECRET_KEY` en producción. Genera una clave segura con: `openssl rand -hex 32`

### Ejemplo de `.env` para Producción
```env
TAQ_SECRET_KEY=tu-clave-secreta-muy-segura-aqui-cambiala
TAQ_DB_ENGINE=postgresql
TAQ_DB_HOST=tu-base-de-datos-host
TAQ_DB_PORT=5432
TAQ_DB_USER=tu_usuario_db
TAQ_DB_PASSWORD=tu_contraseña_segura
TAQ_DB_NAME=taq_produccion
TAQ_LOG_LEVEL=INFO
TAQ_CACHE_ENABLED=true
TAQ_CACHE_TTL=300
TAQ_DEBUG=false
```

---

## 📖 Uso de la API

Todos los endpoint de la API están bajo `/api/v1/` y están documentados interactivamente en:
- **Swagger UI**: `http://tu-servidor/docs`
- **ReDoc**: `http://tu-servidor/redoc`

### Autenticación
La mayoría de los endpoints requieren autenticación mediante **Bearer Token** en el header:

```
Authorization: Bearer <tu_api_key>
```

Puedes obtener tu API key:
1. Registrándote mediante `POST /api/v1/auth/register`
2. Iniciando sesión mediante `POST /api/v1/auth/login`

### Ejemplos Básicos con curl

#### Registro de Nuevo Usuario
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "tu@email.com", "password": "tu_contraseña_segura_123"}'
```

#### Login y Obtención de API Key
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "tu@email.com", "password": "tu_contraseña_segura_123"}'
```

#### Crear una Nueva Investigación
```bash
curl -X POST "http://localhost:8000/api/v1/investigations/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_API_KEY_AQUI" \
  -d '{"seed_type": "domain", "seed_value": "ejemplo.com", "metadata": {"fuente": "test"}}'
```

#### Listar Tus Investigaciones
```bash
curl -X GET "http://localhost:8000/api/v1/investigations/" \
  -H "Authorization: Bearer TU_API_KEY_AQUI"
```

---

## 🎯 Modelos de Deployment y Licencia

### Licencia MIT
TaQ Engine se distribuye bajo la [Licencia MIT](LICENSE), lo que significa que puedes:
- Usarlo comercialmente
- Modificarlo y distribuir las modificaciones
- Usarlo privado o públicamente
- Sin royalties ni restricciones

El único requisito es incluir el aviso de copyright y la licencia en todas las copias o sustancias sustanciales del software.

### Modelo de Sugerencia para SaaS
Si planeas ofrecer TaQ Engine como servicio, considera este modelo:

| Componente | Open Source (GitHub) | Servicio SaaS Gestionado |
|------------|----------------------|--------------------------|
| **Código Base** | ✅ Disponible | ✅ Mismo código |
| **Despliegue** | ❌ Auto-manual | ✅ Un clic / Automático |
| **Actualizaciones** | ❌ Manual | ✅ Automáticas |
| **Soporte** | ❌ Comunitario | ✅ Técnico dedicado |
| **Conectores Premium** | ❌ Requiere config | ✅ Pre-configurados |
| **Monitoreo/Logging** | ❌ Manual | ✅ Integrado |
| **Backups** | ❌ Manual | ✅ Automáticos |
| **Escalabilidad** | ❌ Manual config | ✅ Automática |
| **Seguridad de Infra** | ❌ Tu responsabilidad | ✅ Gestionada |

Tu valor diferencial como proveedor SaaS estaría en ofrecer:
- Deployments confiables y seguros
- Soporte técnico y mantenimiento
- Actualizaciones continuas sin esfuerzo
- Infraestructura preparada para carga de producción
- Integraciones listas para usar
- Cumplimiento de estándares de seguridad (SOC2, ISO27001, etc.)

---

## 📚 Próximos Pasos y Contribución

### Documentación Adicional
- [Guía de Deployment en Producción](docs/production_deployment.md) - Configuración avanzada, Kubernetes, NGINX, seguridad
- [Guía de Desarrollo](docs/development.md) - Cómo contribuir, probar, extender (próximamente)
- [Guía de Conectores](docs/connectors.md) - How to create your own connectors (próximamente)

### ¿Quieres Contribuir?
¡Las contribuciones son bienvenidas! Por favor:
1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

Por favor asegúrate de seguir el [código de conducta](CODE_OF_CONDUCT.md) y las [guías de contribución](CONTRIBUTING.md) (próximamente).

---

## 🙏 Agradecimientos

Gracias a todos los proyectos de código abierto que hacen posible este trabajo:
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pydantic](https://pydantic.dev/)
- [Uvicorn](https://www.uvicorn.org/)
- Y muchas otras bibliotecas increíbles

---

## ❓ Soporte

Para questões, problemas o solicitudes de features:
- **Issues de GitHub**: Usa la sección de Issues en este repositorio
- **Discusiones**: Participa en las discusiones de la comunidad
- **Email**: Para soporte empresarial, contacta a través de los canales oficiales

**Nota**: Este es el núcleo open source de TaQ Engine. Para el servicio gestionado con características empresariales completas, visita [nuestra página de producto] (próximamente).

---

*Última actualización: Junio 2026 | Versión: 1.0.5*