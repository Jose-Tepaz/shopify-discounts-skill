---
name: shopify-discounts
description: Crea, edita, segmenta, programa, activa, desactiva, audita y elimina descuentos de Shopify con la Admin GraphQL API (códigos, automáticos, porcentaje, monto fijo, compra X lleva Y, envío gratis, descuentos de app con Functions, códigos masivos y segmentos de clientes). Úsala siempre que se hable de descuentos, cupones, códigos promocionales, promociones, Black Friday/BFCM, rebajas por segmento o VIP, envío gratis, BOGO o limpieza de descuentos en una tienda Shopify, aunque no se mencione la API.
---

# Descuentos de Shopify

Gestiona descuentos en una tienda real con el menor riesgo posible: leer primero, proponer el cambio exacto, ejecutar solo con confirmación y verificar después. Un descuento mal configurado cuesta dinero en minutos, así que la seguridad pesa más que la velocidad.

Versión de API de referencia: **2026-10** (estable a 2026-11). Si el proyecto fija otra versión, úsala y valida contra esa misma.

## Qué leer según la tarea

| Tarea | Referencia |
|---|---|
| Crear o editar un descuento (básico, BXGY, envío gratis) | [mutaciones](references/mutations.md) |
| Limitar a clientes, segmentos o mercados; crear segmentos | [segmentación](references/targeting-segments.md) |
| Fechas, zonas horarias, combinaciones y límites de la tienda | [programación y combinaciones](references/scheduling-combinations.md) |
| Listar, buscar, auditar, activar/desactivar/eliminar en lote, códigos masivos | [consultas y operaciones masivas](references/queries-bulk.md) |
| Lógica que los descuentos nativos no cubren (escalonados, por volumen, atributos del carrito) | [descuentos con Functions](references/functions.md) |
| Interpretar `userErrors` y fallos | [errores](references/errors.md) |
| Origen de estas prácticas | [fuentes](references/sources.md) |

## Canal de ejecución

Reutiliza lo que ya exista en el proyecto (cliente GraphQL, app con sesión, MCP de la tienda). Si no hay nada, usa Shopify CLI, que no requiere crear una app:

```bash
shopify store auth --store tienda.myshopify.com --scopes read_discounts,write_discounts
shopify store execute --store tienda.myshopify.com --query-file q.graphql --variable-file v.json --json
```

- Pide solo los scopes necesarios: `read_discounts`/`write_discounts`; añade `read_customers`/`write_customers` para segmentos y `read_products` para resolver productos o colecciones.
- Pasa siempre `--store` explícito. Las mutaciones requieren `--allow-mutations`; añádelo únicamente en el paso de ejecución confirmado.
- No pidas tokens en el chat ni los escribas en archivos, URLs o logs. No uses `--verbose` en tiendas reales (puede imprimir datos sensibles).
- Si está disponible el Shopify Dev MCP (`@shopify/dev-mcp`) o la skill oficial `shopify` del AI Toolkit, valida cada operación con su validador de GraphQL antes de ejecutarla. Corrige solo el campo que señale el error y no inventes campos ni valores de enum. Ambas herramientas envían telemetría a Shopify por defecto; menciónalo si el usuario es sensible a ello (`OPT_OUT_INSTRUMENTATION=true`).

## Flujo de trabajo

1. **Identifica la tienda.** Consulta `shop { name myshopifyDomain ianaTimezone currencyCode plan { displayName shopifyPlus } }`. Confirma que es la tienda pretendida y di si es producción o desarrollo. Guarda la zona horaria y la moneda: las necesitas para fechas y montos.
2. **Lee antes de escribir.** Busca si ya existe algo equivalente antes de crearlo:
   - **Códigos:** `codeDiscountNodeByCode(code:)` (no distingue mayúsculas).
   - **Descuentos:** `discountNodes(query:)` por título, etiqueta o estado.
   - **Segmentos:** la lista de `segments`, revisando nombre y consulta.
   
   Si ya existe, propone reutilizarlo o editarlo en vez de duplicarlo. Antes de crear un automático, cuenta los activos (máximo 25).
   
   **Combinaciones recíprocas.** Si el nuevo descuento debe combinarse con otro existente, lee también el `combinesWith` de ese otro. Las combinaciones solo funcionan si ambos lo permiten, así que la actualización del existente forma parte del plan. Advierte que esa actualización también lo abre a otros descuentos de la misma clase.
3. **Traduce la intención a una especificación.** Elige método (código o automático) y tipo (básico, BXGY, envío gratis o app). Resuelve los IDs reales (productos, colecciones, segmentos, mercados) con consultas; nunca los supongas. Prefiere descuentos nativos; usa Functions solo si la lógica lo exige.
4. **Presenta el plan y espera confirmación.** Muestra en lenguaje claro y en la operación exacta:
   - tienda, mutación y variables (en ediciones, el antes → después);
   - valor (recuerda que `percentage: 0.2` es 20 %), alcance (productos/pedido/envío), elegibilidad (todos/segmento/clientes/mercados);
   - fechas en hora local de la tienda **y** en UTC;
   - combinaciones, límites de uso y requisito mínimo;
   - efectos secundarios (p. ej. que `tags` reemplaza todas las etiquetas).
   
   En una tienda real, ejecuta solo tras un "sí" explícito del usuario para ese cambio concreto. Una aprobación no se extiende a cambios posteriores.
5. **Ejecuta** la mutación seleccionando siempre `userErrors { field code message }`. Shopify responde HTTP 200 aunque la mutación falle: el éxito exige payload no nulo, `userErrors` vacío y ausencia de `errors` de primer nivel.
6. **Verifica leyendo de vuelta** el descuento (`status`, `startsAt`, `endsAt`, valor, `context`, `combinesWith`, `codesCount`) y reporta qué se pidió, qué aceptó Shopify y qué quedó configurado. Si algo no coincide, dilo; no lo maquilles.

Las consultas de solo lectura (listar, auditar, contar) no necesitan confirmación.

## Reglas que evitan los errores más caros

- **Desactivar antes que eliminar.** La eliminación es irreversible y borra el historial de uso. Elimina solo si el usuario lo pide de forma explícita, mostrando cuántos y cuáles se borrarán.
- **Respaldo antes de cualquier eliminación.** Shopify no tiene papelera para descuentos. Antes de borrar, exporta la configuración completa de lo que se va a eliminar, con sus códigos. Para pocos descuentos basta una consulta paginada guardada en JSON; para muchos, usa `bulkOperationRunQuery` (ver [consultas y operaciones masivas](references/queries-bulk.md#respaldo-antes-de-eliminar)). Guarda el archivo junto al plan.
- **Muchos códigos = un descuento + códigos de canje.** Para 500 códigos únicos crea un solo descuento y añade los códigos con `discountRedeemCodeBulkAdd` en lotes de ≤250, sondeando `discountRedeemCodeBulkCreation` hasta `done` y revisando `failedCount`. No crees un descuento por código.
  - `scripts/redeem_codes.py` genera y trocea los códigos.
  - Con `--exclude`, evita colisiones con códigos existentes.
  - Si el plan se ejecutará fuera de esta sesión, copia el script junto a los archivos.
- **Operaciones en lote por búsqueda:** ejecuta primero la misma búsqueda como consulta, muestra cuántos coinciden y algunos ejemplos, y solo entonces lanza la mutación masiva. Usa un único argumento de destino (`ids`, `search` o `savedSearchId`).
- **Marca lo que crea el agente.** Usa títulos con convención clara (p. ej. `BFCM 2026 · 20% sitio · VIP`) y una etiqueta propia si el usuario la acepta. No modifiques en lote descuentos que el agente no creó sin confirmación por elemento o por lista revisada.
- **Fechas con zona horaria.** Convierte desde `ianaTimezone` y envía ISO 8601 con offset o en UTC. "Empieza el viernes a medianoche" significa medianoche en la zona de la tienda. Comprueba que `endsAt` sea posterior a `startsAt`.
- **Tipo inmutable.** No se puede convertir un descuento de código en automático ni un básico en BXGY: hay que crear uno nuevo (y desactivar el anterior). Avísalo antes de proponer el cambio.
- **Reintentos seguros.** Ante `THROTTLED`, 429 o 503, espera (≥1 s, exponencial) y reintenta. Antes de reintentar una creación, comprueba que no se creó ya; si no, duplicarás descuentos.
- **No uses campos obsoletos:** `customerSelection` → `context`; `functionId` → `functionHandle`; `discountClass` → `discountClasses`; `automaticDiscountNodes` → `discountNodes(query:"method:automatic")`.

## Forma del reporte final

```
Tienda: tienda.myshopify.com (producción)
Acción: creado descuento de código "VERANO20"
ID: gid://shopify/DiscountCodeNode/123
Valor: 20 % en colección "Verano" · mínimo $500 MXN
Elegibilidad: segmento "Clientes recurrentes" (gid://shopify/Segment/456)
Vigencia: 2026-12-01 00:00 America/Mexico_City (06:00Z) → 2026-12-15 23:59 (05:59Z del 16) · estado SCHEDULED
Combina con: envío · Límite: 1 uso por cliente, 1000 totales
Verificado: sí (lectura posterior coincide)
```

Si algo quedó pendiente (un job asíncrono sin terminar, códigos fallidos), indícalo de forma explícita con el siguiente paso.
