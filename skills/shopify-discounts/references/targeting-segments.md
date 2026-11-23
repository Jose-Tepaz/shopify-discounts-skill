# Segmentación: a quién aplica un descuento

## `context` (sustituye a `customerSelection`, que está obsoleto)

`DiscountContextInput` acepta un solo modo:

| Modo | Valor |
|---|---|
| Todos los compradores | `"context": { "all": "ALL" }` |
| Clientes específicos | `"context": { "customers": { "add": ["gid://shopify/Customer/1"], "remove": [] } }` |
| Segmentos | `"context": { "customerSegments": { "add": ["gid://shopify/Segment/2"] } }` |
| Mercados | `"context": { "markets": { "add": ["gid://shopify/Market/3"] } }` |

- En las ediciones, `add` y `remove` son deltas.
- No mezcles `all` con listas.
- Un código admite como máximo 100 clientes, productos o variantes específicos en total. Para audiencias más grandes, usa un segmento.
- En POS de ubicaciones Pro, los descuentos se aplican automáticamente cuando el contexto no es ALL.
- Al leer de vuelta, usa estos fragmentos:
  - `context { ... on DiscountCustomerSegments { segments { id name } } }`
  - `... on DiscountCustomers { customers { id } }`
  - `... on DiscountMarkets { markets(first: 10) { nodes { id name } } }`

Para segmentar por **destino de envío** en descuentos de envío gratis, usa `destination.countries`. Para segmentar por **mercado**, usa `context.markets`.

## Segmentos de clientes

Un segmento es dinámico: Shopify recalcula quién pertenece. Por eso es preferible a listas fijas de clientes.

**Buscar uno existente** antes de crear (los nombres son únicos):

```graphql
query { segments(first: 50) { nodes { id name query } } }
```

**Previsualizar el tamaño** antes de usarlo y mostrarlo al usuario:

```graphql
query($q: String!) { customerSegmentMembers(first: 1, query: $q) { totalCount } }
```

Si `totalCount` no está disponible en la versión, cuenta paginando o informa "tamaño no confirmado".

**Crear** (requiere `write_customers`):

```graphql
mutation($name: String!, $query: String!) {
  segmentCreate(name: $name, query: $query) {
    segment { id name query }
    userErrors { field message }
  }
}
```

Existen también `segmentUpdate(id, name, query)` y `segmentDelete(id)`. Antes de modificar un segmento, revisa si lo usan otros descuentos o campañas: el cambio los afecta a todos.

## Lenguaje de consulta de segmentos (ShopifyQL, solo WHERE)

**Operadores:**
- comparación: `=` `!=` `>` `>=` `<` `<=`;
- rangos y listas: `BETWEEN a AND b`, `CONTAINS`, `NOT CONTAINS`, `MATCHES`, `NOT MATCHES`;
- lógicos: `AND`, `OR` y paréntesis (AND tiene precedencia).

Una consulta admite como máximo 10 condiciones.

**Valores:**
- Las cadenas van entre comillas simples.
- Los enums distinguen mayúsculas (`'SUBSCRIBED'`).
- `customer_tags` no distingue mayúsculas.

**Fechas:**
- Formatos: `2026-11-01`, offsets (`-7d`, `-2w`, `-3m`, `-1y`), `today`, `yesterday`.
- Se interpretan en la zona horaria de la tienda.
- El formato `30_days_ago` está obsoleto.

| Objetivo | Consulta |
|---|---|
| Clientes VIP por etiqueta | `customer_tags CONTAINS 'vip'` |
| Recurrentes | `number_of_orders >= 2` |
| Alto valor | `amount_spent >= 5000` |
| Primera compra pendiente | `number_of_orders = 0` |
| Inactivos 90 días (win-back) | `last_order_date < -90d AND number_of_orders >= 1` |
| Suscritos a email en México | `email_subscription_status = 'SUBSCRIBED' AND customer_countries CONTAINS 'MX'` |
| Compraron cierta categoría el último año | `products_purchased MATCHES (tag = 'calzado', date >= -12m)` |
| Compraron un producto | `products_purchased MATCHES (id = 1234567890)` |
| Carrito abandonado reciente | `abandoned_checkout_date >= -7d` |
| Cumpleaños hoy (metacampo) | `anniversary('metafields.facts.birth_date') = today` |
| Nuevos registros | `customer_added_date >= -30d` |
| Gasto previsto alto | `predicted_spend_tier = 'HIGH'` |

**Otros atributos:**
- `customer_cities`, `customer_regions`, `customer_language`, `customer_email_domain`;
- `sms_subscription_status`, `customer_account_status`, `rfm_group`;
- `first_order_date`, `orders_placed(...)`, `companies`;
- `storefront_event.product_viewed MATCHES (...)`, `shopify_email.opened MATCHES (...)`.

Ante cualquier duda de sintaxis, valida la consulta creando el segmento en una tienda de desarrollo o con `segmentFilters` / `segmentValueSuggestions`.

## Patrones de segmentación

- **Código exclusivo VIP:** crea o reutiliza el segmento, crea un descuento de código con `context.customerSegments` y `appliesOncePerCustomer: true`. Aunque el código se filtre, solo funciona para el segmento.
- **Bienvenida:** usa el segmento `number_of_orders = 0` con un código y `appliesOncePerCustomer`.
- **Win-back escalonado:** crea varios segmentos por inactividad (90, 180 días) con descuentos distintos. Revisa que no se solapen o que el solapamiento sea intencional.
- **B2B o mayoristas:** usa un segmento por `companies` o por etiqueta. Recuerda que los catálogos B2B tienen precios propios, que pueden ser mejor opción que un descuento.
