# Fuentes (revisadas el 2026-11-23)

La documentación oficial es la fuente de verdad sobre campos, versiones y límites. Los repositorios son ejemplos de buenas prácticas. Ante una discrepancia, valida contra el esquema de la versión que uses. Para obtener el markdown de una página de shopify.dev, añade `.md` a la URL.

## Documentación oficial
- Descuentos (visión general): https://shopify.dev/docs/apps/build/discounts
- Versionado de la API (2026-10 es la estable actual): https://shopify.dev/docs/api/usage/versioning
- Mutaciones e inputs: `https://shopify.dev/docs/api/admin-graphql/2026-10/mutations/<nombre>` y `.../input-objects/<nombre>` (por ejemplo `DiscountCodeBasicInput`, `DiscountContextInput`, `DiscountCombinesWithInput`)
- `discountNodes` y sus filtros de búsqueda: https://shopify.dev/docs/api/admin-graphql/2026-10/queries/discountNodes
- Códigos de error: https://shopify.dev/docs/api/admin-graphql/2026-10/enums/DiscountErrorCode
- Lenguaje de segmentos: https://shopify.dev/docs/api/shopifyql/segment-query-language-reference
- Límites de tasa: https://shopify.dev/docs/apps/build/apis/graphql-admin/rate-limits
- Discount Function API: https://shopify.dev/docs/api/functions/latest/discount
- Shopify CLI `store execute`: https://shopify.dev/docs/api/shopify-cli/store/store-execute
- Combinaciones (Help Center): https://help.shopify.com/en/manual/discounts/discount-combinations
- Límites de códigos (Help Center): https://help.shopify.com/en/manual/discounts/discount-methods/discount-codes

## Repositorios y qué se tomó de cada uno

- **Shopify/shopify-ai-toolkit**: el kit oficial para agentes. De aquí salen:
  - validar cada operación contra el esquema antes de ejecutarla, con un máximo de 3 correcciones y sin inventar campos;
  - usar la versión estable más reciente, la misma para buscar, validar y ejecutar;
  - pedir scopes mínimos;
  - pedir confirmación explícita antes de cualquier mutación;
  - pasar `--store` siempre.
- **@shopify/dev-mcp**: validador de GraphQL (`validate_graphql_codeblocks`) y búsqueda de documentación. No modifica tiendas.
- **Shopify/discounts-reference-app**: el modelo de seguridad para tiendas reales:
  - simulación sin mutaciones;
  - verificar la identidad de la tienda antes de la primera escritura;
  - claves naturales y marcas de propiedad para no duplicar;
  - no tocar recursos sin marca.
  
  También la configuración de Functions en metacampos JSON y la normalización de IDs a GID.
- **Shopify/function-examples**: plantillas de Functions. Se generan con la CLI y se prueban en local antes de desplegar.
- **Shopify/shopify-app-js**: cliente oficial (sustituye a `shopify-api-js`, que está archivado). Reintentos solo para 429/503 y registro de avisos de deprecación. El throttling de GraphQL hay que manejarlo aparte.
- **40RTY-ai/shopify-admin-skills**: skills comunitarias para la API de administración de Shopify.
  - Lo adoptado: simulación por defecto, salida con progreso y sección explícita de seguridad.
  - Lo evitado: versión fija antigua, uso de `customerSelection`, un descuento por cada código y eliminación en lugar de desactivación.
- **callobuzz/cob-shopify-mcp** y **benwmerritt/shopify-mcp**: MCPs comunitarios. De ellos se tomó:
  - modo solo lectura por defecto;
  - herramientas de riesgo desactivadas hasta revisarlas;
  - lectura posterior a cada escritura para detectar rechazos silenciosos;
  - registro de auditoría.

## Pendiente de confirmar en la versión usada
- El scope exacto de las consultas `segments` / `segment` (probablemente `read_customers`) y si `context.markets` requiere `read_markets`.
- El efecto exacto de `discountCodeDeactivate` sobre `endsAt`. Verifícalo leyendo el descuento después.
- Si `customerSegmentMembers` expone `totalCount`.
