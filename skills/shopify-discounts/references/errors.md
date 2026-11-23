# Errores frecuentes

Las mutaciones devuelven HTTP 200 aunque fallen. Hay que revisar tres cosas:

1. `errors` de primer nivel: errores de sintaxis, permisos o throttling.
2. `data.<mutación>` nulo.
3. `userErrors[]` con `field`, `code` y `message`.

Reporta el `code` y el `field` tal cual; no los parafrasees como si el cambio hubiera funcionado.

| Código | Causa habitual | Qué hacer |
|---|---|---|
| `TAKEN` | El código ya existe en la tienda (en cualquier descuento) | Consulta `codeDiscountNodeByCode`. Si es el mismo descuento, no hagas nada; si no, propone otro código |
| `ACTIVE_PERIOD_OVERLAP` | Más de 25 automáticos activos en ese periodo | Lista los activos y los programados; propone desactivar o reprogramar |
| `MAX_APP_DISCOUNTS` | Límite de descuentos de app | Igual que el anterior |
| `END_DATE_BEFORE_START_DATE` | `endsAt` ≤ `startsAt` | Revisa la conversión de zona horaria |
| `VALUE_OUTSIDE_RANGE` | Porcentaje fuera de 0–1 (p. ej. 20 en lugar de 0.2) o monto negativo | Corrige la escala |
| `MINIMUM_SUBTOTAL_AND_QUANTITY_RANGE_BOTH_PRESENT` | Se enviaron los dos mínimos | Deja uno solo |
| `APPLIES_ON_NOTHING` | `appliesOnOneTimePurchase` y `appliesOnSubscription` están en false | Activa al menos uno |
| `MULTIPLE_RECURRING_CYCLE_LIMIT_FOR_NON_SUBSCRIPTION_ITEMS` | `recurringCycleLimit` ≠ 1 sin suscripciones | Ponlo en 1 u omítelo |
| `INVALID_COMBINES_WITH_FOR_DISCOUNT_CLASS` | Combinación imposible para la clase (p. ej. envío + envío) | Ajusta `combinesWith` |
| `PRODUCT_DISCOUNTS_WITH_TAGS_ON_SAME_CART_LINE_NOT_ENTITLED` | Apilamiento en la misma línea sin ser Plus | Quita la opción |
| `TOO_MANY_TAGS` / `INVALID_TAG_LENGTH` | Más de 5 etiquetas o más de 255 caracteres | Reduce |
| `TOO_MANY_ARGUMENTS` | Bulk con `ids` y `search` a la vez | Usa uno solo |
| `MULTIPLE_FUNCTION_IDENTIFIERS` / `MISSING_FUNCTION_IDENTIFIER` | Se enviaron `functionHandle` y `functionId`, o ninguno | Usa solo `functionHandle` |
| `EXCEEDED_MAX` | Más de 100 entidades específicas, o más de 250 elementos en una lista | Usa una colección o un segmento, o divide en lotes |
| `BLANK` / `MISSING_ARGUMENT` | Falta un campo obligatorio | Revisa los obligatorios en [mutaciones](mutations.md) |
| `INTERNAL_ERROR` | Error de Shopify | Lee el estado antes de reintentar una sola vez |

**Errores de nivel superior:**
- `THROTTLED`: espera según `throttleStatus` y reintenta.
- `ACCESS_DENIED`: falta un scope. Pide re-autenticar solo con el scope que falta.
- `MAX_COST_EXCEEDED`: reduce `first` o los campos seleccionados.
- Un aviso de deprecación (encabezado `X-Shopify-API-Deprecated-Reason`) indica que la versión o el campo usado tiene reemplazo. Actualiza la consulta.
