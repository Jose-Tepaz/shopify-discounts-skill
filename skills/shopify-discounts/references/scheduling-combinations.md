# Programación, combinaciones y límites

## Programar

- `startsAt` es obligatorio. `endsAt` es opcional y `null` significa que no expira. Ambos van en ISO 8601. Shopify acepta un offset (`2026-12-01T00:00:00-06:00`) y responde en UTC (`Z`).
- **Un descuento futuro no necesita activarse**: con `startsAt` en el futuro, su estado es `SCHEDULED` y pasa solo a `ACTIVE`. Al pasar `endsAt`, queda `EXPIRED`.
- Los estados (`DiscountStatus`) son `ACTIVE`, `SCHEDULED` y `EXPIRED`.

**Conversión de fechas:**

1. Obtén `shop { ianaTimezone }`. Interpreta las fechas del usuario en esa zona salvo que indique otra.
2. Convierte con la base de datos de zonas horarias, no con offsets fijos: el horario de verano cambia el offset.

```bash
python3 -c "from datetime import datetime; from zoneinfo import ZoneInfo as Z; d=datetime(2026,11,27,0,0,tzinfo=Z('America/Mexico_City')); print(d.isoformat(), d.astimezone(Z('UTC')).isoformat())"
```

3. Muestra ambas horas en el plan: "viernes 27 nov 00:00 hora de la tienda = 06:00 UTC".
4. Para "hasta el domingo inclusive", usa `endsAt` a las 23:59:59 local del domingo.

**Campañas por fases** (p. ej. 30 % el BF, 20 % el fin de semana, 10 % el lunes):
- Crea un descuento por fase con fechas contiguas y sin solape. No edites un solo descuento a mano en cada transición.
- Si las fases son códigos distintos, comunica cada código.
- Si son automáticos, verifica que no haya dos activos a la vez que se pisen.

**Pausar o extender:**
- Para extender, edita `endsAt`.
- Para pausar ya, usa `discount*Deactivate`.
- Para reanudar, usa `discount*Activate` o ajusta `startsAt` y `endsAt`. Lee el estado después.

**Programación recurrente** (p. ej. "cada lunes"): Shopify no la tiene de forma nativa. Las opciones son:
- crear por adelantado un descuento por ocurrencia, o
- usar un proceso externo (cron, Shopify Flow) que active y desactive.

Explica la opción elegida.

## Combinaciones (`combinesWith`)

```json
"combinesWith": { "productDiscounts": false, "orderDiscounts": false, "shippingDiscounts": true }
```

- Por defecto **no combina con nada**: todos los campos son `false`.
- La combinación debe permitirse **en ambos descuentos**. Si A dice que combina con descuentos de pedido pero B (de pedido) no lo permite, no se combinan. Al habilitar una combinación, revisa y, si hace falta, actualiza el otro descuento.

**Qué clases pueden combinarse:**

| Combinación | Disponibilidad |
|---|---|
| Pedido + envío, producto + envío | todas las tiendas |
| Producto + producto en líneas distintas | todas las tiendas |
| Producto + pedido, pedido + pedido | tiendas sin checkout.liquid |
| Producto + producto en la **misma línea** | Shopify Plus, con `productDiscountsWithTagsOnSameCartLine` y etiquetas recíprocas |
| Envío + envío | nunca |

**Orden de cálculo:**
1. Primero los descuentos de producto, después los de pedido y al final los de envío.
2. Un descuento porcentual de pedido se calcula sobre el subtotal original.
3. Un descuento de monto fijo de pedido se aplica después.

Cuando dos descuentos no pueden combinarse, Shopify aplica el mejor para el cliente.

Las combinaciones solo funcionan en Online Store, Storefront API y POS. No funcionan en checkouts externos como Facebook o Google.

## Límites de la tienda

| Límite | Valor |
|---|---|
| Descuentos automáticos activos | 25, incluidos los de app (error `ACTIVE_PERIOD_OVERLAP` / `MAX_APP_DISCOUNTS`) |
| Códigos por pedido | 5 de producto/pedido + 1 de envío |
| Códigos únicos por tienda | 20,000,000 acumulados; eliminar libera espacio |
| Clientes/productos/variantes específicos por código | 100 |
| Códigos por llamada a `discountRedeemCodeBulkAdd` | 250 |
| Etiquetas por descuento | 5, de hasta 255 caracteres |
| Elementos en cualquier argumento lista | 250 |
| Paginación | hasta 25,000 objetos; usa `bulkOperationRunQuery` si necesitas más |
| Funciones de descuento activas | 25 |

## Límites de tasa (costo GraphQL)

- Puntos por segundo por app y tienda: Standard 100, Advanced 200, Plus 1000, Enterprise 2000.
- Una mutación cuesta 10 puntos.
- El costo máximo de una consulta es 1000.

**Ritmo de llamadas:**
- Cada respuesta trae `extensions.cost.throttleStatus { currentlyAvailable restoreRate }`. Si lo disponible no alcanza el costo de la siguiente llamada, espera `(costo - disponible) / restoreRate` segundos.
- Ante `THROTTLED` (puede llegar con HTTP 200), 429 o 503, aplica backoff exponencial desde 1 s.
- Usa `Shopify-GraphQL-Cost-Debug: 1` para ver el desglose del costo al afinar consultas.
