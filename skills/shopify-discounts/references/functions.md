# Descuentos de app con Shopify Functions

## ¿Hace falta una Function?

Usa descuentos **nativos** (básico, BXGY, envío gratis) siempre que alcancen: no requieren app, se ven y se editan en el admin, y no tienen riesgo de fallo en el checkout.

Una Function está justificada cuando la lógica no se puede expresar de forma nativa:
- niveles por volumen o gasto (compra 3 → 10 %, 5 → 15 %, 10 → 20 %);
- condiciones sobre atributos del carrito, metacampos de producto o cliente, o tipo de entrega;
- un solo descuento que toque productos **y** envío;
- validación propia de códigos (aceptar o rechazar códigos introducidos).

Si el usuario pide algo de esta lista, explica que requiere una app con extensión y que su desarrollo y despliegue van aparte del cambio en la tienda.

## Discount Function API (unificada)

Las antiguas APIs separadas de Product, Order y Shipping Discount están obsoletas; no las uses salvo que el usuario las mencione. Los targets actuales son:

| Target | Devuelve |
|---|---|
| `cart.lines.discounts.generate.run` | `productDiscountsAdd`, `orderDiscountsAdd` (estrategia `FIRST` o `MAXIMUM`), `enteredDiscountCodesAccept`, `enteredDiscountCodesReject` |
| `cart.delivery-options.discounts.generate.run` | `deliveryDiscountsAdd` |
| `*.fetch` | acceso a red, solo para apps personalizadas Enterprise |

**Datos de entrada que recibe la Function:**
- `discount.discountClasses`;
- `discount.metafield` (la configuración);
- `cart`, `enteredDiscountCodes`, `triggeringDiscountCode`, `localization`, `shop`.

**Comportamiento:**
- Las Functions corren en paralelo y no se ven entre sí.
- Si fallan, el descuento simplemente no se aplica.
- No se re-ejecutan en ediciones de pedidos ni en cobros recurrentes de suscripción.
- Rechazar un código lo quita de todo el carrito.

## Pasos

1. Genera la extensión con `shopify app generate extension --template discount`, partiendo de las plantillas de `Shopify/function-examples` o de `Shopify/discounts-reference-app`. No copies archivos a mano.
2. En `shopify.extension.toml`, define un bloque `[[extensions.targeting]]` por target (`target`, `input_query`, `export`). En `shopify.app.toml`, incluye `write_discounts` en los scopes.
3. Haz la Function **configurable por metacampo** en lugar de fijar valores en el código. Así el comercio puede cambiar porcentajes sin redeploy.
4. Prueba en local con `shopify app function run --input=input.json --export=<nombre>` y en una tienda de desarrollo con `shopify app dev`.
5. Despliega con `shopify app deploy`.
6. Crea el nodo de descuento:

```graphql
mutation {
  discountAutomaticAppCreate(automaticAppDiscount: {
    title: "Volumen: 10/15/20 %"
    functionHandle: "volume-discount"
    discountClasses: [PRODUCT]
    startsAt: "2026-12-01T06:00:00Z"
    combinesWith: { orderDiscounts: false, productDiscounts: false, shippingDiscounts: true }
    metafields: [{
      namespace: "$app"
      key: "function-configuration"
      type: "json"
      value: "{\"tiers\":[{\"min\":3,\"pct\":10},{\"min\":5,\"pct\":15},{\"min\":10,\"pct\":20}]}"
    }]
  }) {
    automaticAppDiscount { discountId title status }
    userErrors { field code message }
  }
}
```

**Puntos a cuidar al crear el nodo:**
- Usa `functionHandle`, el handle del toml. `functionId` está obsoleto; enviar los dos da `MULTIPLE_FUNCTION_IDENTIFIERS`.
- `discountClasses` es obligatorio. Pon solo las clases para las que la Function devuelve operaciones.
- Para editar la configuración, actualiza el metacampo existente pasando su `id`. No crees uno nuevo.
- Los descuentos de app cuentan para el límite de 25 automáticos activos.
