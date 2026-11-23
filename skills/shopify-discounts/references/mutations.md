# Crear y editar descuentos (Admin GraphQL 2026-10)

Todas las mutaciones requieren `write_discounts`. Selecciona siempre `userErrors { field code message }`.

## Índice
- [Elegir mutación](#elegir-mutación)
- [Campos de entrada](#campos-de-entrada)
- [Básico por código](#básico-por-código)
- [Básico automático](#básico-automático)
- [Compra X lleva Y (BXGY)](#compra-x-lleva-y-bxgy)
- [Envío gratis](#envío-gratis)
- [Editar](#editar)
- [Activar, desactivar, eliminar](#activar-desactivar-eliminar)

## Elegir mutación

| Tipo | Código | Automático | Argumento |
|---|---|---|---|
| Básico (% o monto en productos o pedido) | `discountCodeBasicCreate` / `Update` | `discountAutomaticBasicCreate` / `Update` | `basicCodeDiscount` / `automaticBasicDiscount` |
| Compra X lleva Y | `discountCodeBxgyCreate` / `Update` | `discountAutomaticBxgyCreate` / `Update` | `bxgyCodeDiscount` / `automaticBxgyDiscount` |
| Envío gratis | `discountCodeFreeShippingCreate` / `Update` | `discountAutomaticFreeShippingCreate` / `Update` | `freeShippingCodeDiscount` / `freeShippingAutomaticDiscount` |
| App (Function) | `discountCodeAppCreate` / `Update` | `discountAutomaticAppCreate` / `Update` | `codeAppDiscount` / `automaticAppDiscount` |

- Los de código devuelven `codeDiscountNode { id }` (`gid://shopify/DiscountCodeNode/…`).
- Los automáticos devuelven `automaticDiscountNode { id }` (`gid://shopify/DiscountAutomaticNode/…`).
- Los de app devuelven `codeAppDiscount` / `automaticAppDiscount { discountId }`.
- Las ediciones usan `id` más el mismo argumento. Usar la mutación de un tipo con el ID de otro da "not found".

**Clase resultante en los nativos:**
- Básico con `items.all: true` → ORDER (descuento al pedido).
- Básico con productos o colecciones → PRODUCT.
- Envío gratis → SHIPPING.

## Campos de entrada

| Input | Obligatorios al crear | Opcionales relevantes |
|---|---|---|
| `DiscountCodeBasicInput` | `title`, `code`, `context`, `customerGets`, `startsAt` | `endsAt`, `minimumRequirement`, `combinesWith`, `usageLimit`, `appliesOncePerCustomer`, `recurringCycleLimit`, `tags` |
| `DiscountAutomaticBasicInput` | `title`, `customerGets`, `startsAt` | `context`, `endsAt`, `minimumRequirement`, `combinesWith`, `recurringCycleLimit`, `tags` |
| `DiscountCodeBxgyInput` | `title`, `code`, `context`, `customerBuys`, `customerGets`, `startsAt` | `endsAt`, `usesPerOrderLimit`, `usageLimit`, `appliesOncePerCustomer`, `combinesWith`, `tags` |
| `DiscountAutomaticBxgyInput` | `title`, `customerBuys`, `customerGets`, `startsAt` | `context`, `endsAt`, `usesPerOrderLimit`, `combinesWith`, `tags` |
| `DiscountCodeFreeShippingInput` | `title`, `code`, `context`, `startsAt` | `destination`, `maximumShippingPrice`, `minimumRequirement`, `appliesOnOneTimePurchase`, `appliesOnSubscription`, `recurringCycleLimit`, `usageLimit`, `appliesOncePerCustomer`, `combinesWith`, `endsAt`, `tags` |
| `DiscountAutomaticFreeShippingInput` | `title`, `startsAt` | igual que el de código, sin `code`, `usageLimit` ni `appliesOncePerCustomer` |

### Semántica de los valores

**`customerGets.value`** admite exactamente una de estas formas:
- `percentage: 0.15`, que es una fracción entre 0 y 1 (0.15 = 15 %);
- `discountAmount: { amount: "100.00", appliesOnEachItem: false }`;
- `discountOnQuantity: { quantity: "2", effect: { percentage: 1.0 } }`, solo en BXGY.

**`customerGets.items`** admite:
- `all: true`, que no se permite en BXGY;
- `products: { productsToAdd, productsToRemove, productVariantsToAdd, productVariantsToRemove }`;
- `collections: { add, remove }`.

**`appliesOnEachItem`:** con `true`, el monto se descuenta de cada artículo elegible; con `false`, se reparte una sola vez.

**`minimumRequirement`** acepta una sola condición:
- `subtotal: { greaterThanOrEqualToSubtotal: "500" }`, o
- `quantity: { greaterThanOrEqualToQuantity: "3" }`.

Enviar las dos da `MINIMUM_SUBTOTAL_AND_QUANTITY_RANGE_BOTH_PRESENT`.

**Límites de uso:**
- `usageLimit` es el total de usos por código, sumando todos los clientes; `null` significa ilimitado. Con códigos de canje masivos, aplica a cada código.
- `appliesOncePerCustomer: true` permite un solo uso por cliente.

**Formato de números:** los tipos `Decimal` y `UnsignedInt64` se envían como string (`"500.00"`, `"3"`). Los montos se expresan en la moneda de la tienda.

**Suscripciones:**
- `appliesOnSubscription` y `appliesOnOneTimePurchase` van dentro de `customerGets` en los básicos y BXGY, y en el nivel superior en envío gratis y app.
- Ponerlos ambos en `false` da `APPLIES_ON_NOTHING`.
- `recurringCycleLimit`: `0` significa indefinido y `N` los primeros N cobros. Debe ser 1 si el descuento no aplica a suscripciones.

**Valores mínimos:** evita descuentos de $0 o 0 %, porque pueden fallar en el checkout.

## Básico por código

```graphql
mutation CrearCodigo($basicCodeDiscount: DiscountCodeBasicInput!) {
  discountCodeBasicCreate(basicCodeDiscount: $basicCodeDiscount) {
    codeDiscountNode {
      id
      codeDiscount {
        ... on DiscountCodeBasic { title status startsAt endsAt codes(first: 5) { nodes { code } } }
      }
    }
    userErrors { field code message }
  }
}
```

```json
{
  "basicCodeDiscount": {
    "title": "VERANO20 · 20% colección Verano",
    "code": "VERANO20",
    "startsAt": "2026-12-01T06:00:00Z",
    "endsAt": "2026-12-16T05:59:59Z",
    "context": { "all": "ALL" },
    "customerGets": {
      "value": { "percentage": 0.2 },
      "items": { "collections": { "add": ["gid://shopify/Collection/123"] } }
    },
    "minimumRequirement": { "subtotal": { "greaterThanOrEqualToSubtotal": "500.00" } },
    "combinesWith": { "productDiscounts": false, "orderDiscounts": false, "shippingDiscounts": true },
    "usageLimit": 1000,
    "appliesOncePerCustomer": true
  }
}
```

Para un monto fijo al pedido completo, usa `"value": { "discountAmount": { "amount": "150.00", "appliesOnEachItem": false } }` con `"items": { "all": true }`.

## Básico automático

```graphql
mutation CrearAutomatico($automaticBasicDiscount: DiscountAutomaticBasicInput!) {
  discountAutomaticBasicCreate(automaticBasicDiscount: $automaticBasicDiscount) {
    automaticDiscountNode {
      id
      automaticDiscount { ... on DiscountAutomaticBasic { title status startsAt endsAt } }
    }
    userErrors { field code message }
  }
}
```

Las variables son como las del básico por código, pero sin `code`, `usageLimit` ni `appliesOncePerCustomer`. El descuento se aplica sin que el cliente escriba nada. Recuerda el máximo de 25 automáticos activos.

## Compra X lleva Y (BXGY)

Ejemplo: compra 3 de la colección y lleva 2 con 20 % de descuento, hasta 3 veces por pedido.

```json
{
  "bxgyCodeDiscount": {
    "title": "3x2 parcial colección Verano",
    "code": "LLEVA2",
    "startsAt": "2026-12-01T06:00:00Z",
    "context": { "all": "ALL" },
    "customerBuys": {
      "items": { "collections": { "add": ["gid://shopify/Collection/123"] } },
      "value": { "quantity": "3" }
    },
    "customerGets": {
      "items": { "collections": { "add": ["gid://shopify/Collection/123"] } },
      "value": { "discountOnQuantity": { "quantity": "2", "effect": { "percentage": 0.2 } } }
    },
    "usesPerOrderLimit": 3
  }
}
```

- `effect.percentage: 1.0` hace gratis el artículo (BOGO).
- `customerBuys.value` puede ser `quantity` (compra N piezas) o `amount` (gasta $X).
- `customerGets.value` solo admite `discountOnQuantity`.

## Envío gratis

```json
{
  "freeShippingAutomaticDiscount": {
    "title": "Envío gratis desde $999 MX",
    "startsAt": "2026-12-01T06:00:00Z",
    "destination": { "countries": { "add": ["MX"] } },
    "maximumShippingPrice": "250.00",
    "minimumRequirement": { "subtotal": { "greaterThanOrEqualToSubtotal": "999.00" } },
    "appliesOnOneTimePurchase": true,
    "combinesWith": { "productDiscounts": true, "orderDiscounts": true }
  }
}
```

- Usa `"destination": { "all": true }` para todos los países.
- `maximumShippingPrice: null` cubre cualquier tarifa.
- Para limitar por mercado en lugar de por país, usa `context.markets`.

## Editar

Envía solo los campos que cambian, junto con el `id`:

```json
{
  "id": "gid://shopify/DiscountCodeNode/206265824",
  "basicCodeDiscount": {
    "endsAt": "2026-12-31T05:59:59Z",
    "customerGets": { "value": { "percentage": 0.25 } }
  }
}
```

- Las listas de productos, colecciones y `context` son **deltas** (`add` / `remove`), no reemplazos. Para cambiar la colección, quita la anterior y añade la nueva.
- `tags` (`[String!]`, máximo 5) **reemplaza** todas las etiquetas. Lee primero las actuales y envía la lista completa. Para solo añadir, usa la mutación aparte `tagsAdd(id:, tags:)`, que funciona con cualquier recurso etiquetable; confirma con el validador que acepta IDs de descuento.
- En una creación, `tags` no reemplaza nada. Úsalo para la etiqueta propia del agente o de la campaña, si el usuario la acepta.
- Para quitar el mínimo, envía `"minimumRequirement": { "quantity": { "greaterThanOrEqualToQuantity": null }, "subtotal": { "greaterThanOrEqualToSubtotal": null } }`.
- No se puede cambiar el tipo (básico ↔ BXGY ↔ envío) ni el método (código ↔ automático). Crea uno nuevo y desactiva el anterior.
- Cambiar el código principal (`code`) de un descuento con uso histórico confunde los reportes. Mejor crea otro código.

## Activar, desactivar, eliminar

| Acción | Código | Automático | Reversible |
|---|---|---|---|
| Activar ahora | `discountCodeActivate(id)` | `discountAutomaticActivate(id)` | sí |
| Desactivar (deja de aplicar) | `discountCodeDeactivate(id)` | `discountAutomaticDeactivate(id)` | sí |
| Eliminar | `discountCodeDelete(id)` → `deletedCodeDiscountId` | `discountAutomaticDelete(id)` → `deletedAutomaticDiscountId` | **no** |

- La desactivación ajusta en la práctica el fin de vigencia a "ahora" y el estado pasa a EXPIRED. Confírmalo leyendo `status` y `endsAt` después.
- Para pausar con fecha concreta, actualiza `endsAt` en lugar de desactivar.
- Para operaciones en lote, ve a [consultas y operaciones masivas](queries-bulk.md).
