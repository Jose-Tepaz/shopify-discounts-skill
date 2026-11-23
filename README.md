# shopify-discounts

Skill para Claude que gestiona descuentos de Shopify con la Admin GraphQL API (versión 2026-10). Cubre todo el ciclo de vida de un descuento:

- **Crear y editar:** porcentaje, monto fijo, compra X lleva Y, envío gratis y descuentos de app con Shopify Functions.
- **Segmentar:** por clientes, segmentos dinámicos (ShopifyQL) o mercados.
- **Programar:** fechas en la zona horaria de la tienda y campañas por fases.
- **Combinar** descuentos entre sí, respetando los límites de la tienda.
- **Generar códigos masivos:** un descuento con miles de códigos únicos.
- **Auditar y limpiar:** desactivar, o eliminar con respaldo previo.

La skill prioriza la seguridad en tiendas reales. Primero lee el estado actual y propone el cambio exacto. Solo ejecuta con tu confirmación explícita, y al final lee de nuevo para verificar el resultado.

## Instalación

### Claude Code como plugin (recomendado)

Dentro de `claude`, en una terminal:

```text
/plugin marketplace add Jose-Tepaz/shopify-discounts-skill
/plugin install shopify-discounts@shopify-discounts-skill
```

Para actualizar después: `/plugin marketplace update shopify-discounts-skill`.

### Claude Code copiando la carpeta

```bash
git clone https://github.com/Jose-Tepaz/shopify-discounts-skill.git
cp -R shopify-discounts-skill/skills/shopify-discounts ~/.claude/skills/
```

Para usarla en un solo proyecto, cópiala en `.claude/skills/` dentro de ese proyecto. Después abre una sesión nueva.

### Claude.ai

Descarga `shopify-discounts.skill` desde [Releases](https://github.com/Jose-Tepaz/shopify-discounts-skill/releases), o comprime la carpeta `skills/shopify-discounts`. Luego súbelo en la configuración de Claude.ai, en la sección de skills.

### Otros asistentes (Codex, etc.)

Copia `skills/shopify-discounts` a la carpeta de skills de tu asistente, por ejemplo `~/.codex/skills/`.

## Requisitos para usarla con una tienda

La skill no da acceso a ninguna tienda. Cada persona usa sus propias credenciales.

- **[Shopify CLI](https://shopify.dev/docs/api/shopify-cli)**, para ejecutar operaciones sin crear una app:
  ```bash
  shopify store auth --store tu-tienda.myshopify.com --scopes read_discounts,write_discounts
  ```
  Añade `read_customers,write_customers` para segmentos y `read_products` para limitar por producto o colección.
- **Python 3**, solo para `scripts/redeem_codes.py` (códigos masivos).
- **Opcional, recomendado:** [Shopify Dev MCP](https://shopify.dev/docs/apps/build/ai-toolkit), para validar cada operación GraphQL contra el esquema antes de ejecutarla.

## Ejemplos de uso

```text
Crea un código VIP25 de 25% para clientes que han gastado más de 5000 MXN,
del viernes 27 de noviembre a medianoche al lunes 30 a las 23:59, un uso por cliente.
```

```text
Necesito 1200 códigos únicos de 15% para influencers, prefijo INF-, válidos en diciembre.
```

```text
Audita los descuentos de la tienda y propón cuáles desactivar: caducados, sin uso
o automáticos que ya no sirven.
```

Prueba primero en una tienda de desarrollo (`shopify store create dev`) antes de tocar producción.

## Estructura

```text
skills/shopify-discounts/
├── SKILL.md                  # flujo y reglas de seguridad
├── references/               # se cargan según la tarea
│   ├── mutations.md          # crear/editar por tipo
│   ├── targeting-segments.md # clientes, segmentos, mercados
│   ├── scheduling-combinations.md
│   ├── queries-bulk.md       # auditoría, operaciones masivas, respaldo
│   ├── functions.md          # descuentos de app
│   ├── errors.md
│   └── sources.md            # documentación y repos de origen
├── scripts/redeem_codes.py   # genera y trocea códigos únicos
└── evals/                    # casos de prueba (formato `claude plugin eval`)
```

## Evaluación

En dos rondas de pruebas, con y sin la skill, cumplió el 100 % de los criterios frente al 82 % sin ella. La diferencia está en:

- pedir confirmación antes de cambios;
- desactivar en vez de borrar;
- respaldar antes de eliminar;
- reutilizar segmentos existentes;
- confirmar la zona horaria.

Los casos están en `skills/shopify-discounts/evals/`.

## Limitaciones

- Las operaciones no se han validado contra una tienda real. Algunos detalles marcados en `references/sources.md` deben confirmarse en la versión de API que uses.
- Los descuentos con lógica personalizada (escalonados, por atributos del carrito) requieren desarrollar y desplegar una app con Shopify Functions. La skill explica cómo, pero no lo automatiza.

## Licencia

[MIT](LICENSE)
