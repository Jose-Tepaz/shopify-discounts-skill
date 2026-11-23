# Consultas, auditoría y operaciones masivas

Las lecturas requieren `read_discounts`.

## Listar y buscar

```graphql
query Descuentos($q: String, $after: String) {
  discountNodes(first: 50, query: $q, after: $after, sortKey: ENDS_AT) {
    nodes {
      id
      discount {
        __typename
        ... on DiscountCodeBasic { title status startsAt endsAt asyncUsageCount codesCount { count } totalSales { amount currencyCode } discountClasses tags }
        ... on DiscountCodeBxgy { title status startsAt endsAt asyncUsageCount }
        ... on DiscountCodeFreeShipping { title status startsAt endsAt asyncUsageCount }
        ... on DiscountCodeApp { title status startsAt endsAt discountClasses }
        ... on DiscountAutomaticBasic { title status startsAt endsAt asyncUsageCount discountClasses }
        ... on DiscountAutomaticBxgy { title status startsAt endsAt }
        ... on DiscountAutomaticFreeShipping { title status startsAt endsAt }
        ... on DiscountAutomaticApp { title status startsAt endsAt discountClasses }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
```

Incluye fragmentos para los **8 tipos**. Si cubres solo `DiscountCodeBasic`, la auditoría saldrá incompleta sin que nadie lo note.

**Filtros de `query`** (se combinan con espacios):

| Filtro | Ejemplo |
|---|---|
| estado | `status:active`, `status:scheduled`, `status:expired` |
| método | `method:code`, `method:automatic` |
| tipo | `type:percentage`, `type:fixed_amount`, `type:bxgy`, `type:free_shipping`, `type:app` |
| clase | `discount_class:order` |
| texto | `title:'Black Friday Sale'`, `code:VERANO20` |
| etiqueta | `tag:agente` |
| elegibilidad | `context:segment`, `segment_ids:123` |
| combinaciones | `combines_with:shipping_discounts` |
| fechas (zona de la tienda) | `ends_at:<now`, `starts_at:>'2026-12-01T00:00:00Z'`, `created_at:<'2026-09-24'` |
| uso | `times_used:>100`, `times_used:0` |

**Sintaxis documentada:**
- **Fechas:** solo admiten valores absolutos entre comillas o `now`. Los relativos como `-30d` no están documentados para esta búsqueda, aunque sí existen en el lenguaje de segmentos. Calcula la fecha absoluta, por ejemplo "hace 60 días" desde hoy, y muéstrala en el plan.
- **Comodín `*`:** existe en la sintaxis general de búsqueda (`norm*`), pero no está documentado para `title` ni `code`.

**Antes de depender de una búsqueda dudosa:**
1. Ejecútala como lectura y revisa que el conteo y la muestra tengan sentido.
2. Si devuelve algo inesperado, filtra del lado del cliente después de leer.

**Búsquedas puntuales:**
- `codeDiscountNodeByCode(code: "verano20")` no distingue mayúsculas y responde si un código ya existe.
- `discountNode(id:)` busca por ID de cualquier tipo.
- `discountNodesCount(query:)` cuenta resultados (por defecto hasta 10,000).

**Métricas:**
- `asyncUsageCount` y `totalSales` se actualizan de forma asíncrona y pueden ir retrasados.
- Para análisis de ingresos por descuento, usa los pedidos (`orders(query:"discount_code:VERANO20")`) o ShopifyQL de analytics.

## Auditorías comunes

- **Caducados pero visibles:** `status:expired`. Propón desactivarlos o archivarlos con etiqueta; elimínalos solo si el usuario lo pide.
- **Nunca usados tras 60 días:** `times_used:0 status:active created_at:<'<hoy menos 60 días, AAAA-MM-DD>'`. `times_used` se actualiza de forma asíncrona, así que confirma con `asyncUsageCount` en la lectura.
- **Sin fecha de fin y muy generosos** (riesgo de fuga): básicos activos con `endsAt: null` y porcentaje ≥ 0.3. Filtra en cliente después de leer.
- **Automáticos activos cerca del límite de 25:** `method:automatic status:active`, más la lista de los programados que se activarán.
- **Combinaciones no recíprocas:** lee `combinesWith` de los activos y cruza las clases.

Presenta los hallazgos como tabla (título, tipo, estado, fechas, usos, acción sugerida) antes de proponer cambios.

## Códigos de canje masivos (cientos o miles de códigos únicos)

1. **Evita colisiones antes de generar.** Un código que ya exista en la tienda, en cualquier descuento, falla con `TAKEN`.
   - Si el prefijo puede haberse usado antes, exporta los códigos existentes con el respaldo masivo (ver [respaldo](#respaldo-antes-de-eliminar)) y pásalos con `--exclude`.
   - Como mínimo, comprueba el código semilla con `codeDiscountNodeByCode`.
2. Genera los códigos y divídelos en lotes de ≤250:
   ```bash
   python3 <ruta-de-la-skill>/scripts/redeem_codes.py --count 2000 --prefix BF26- --out codes/ [--exclude existentes.txt]
   ```
   El script escribe archivos `batch-NNN.json`, listos como variables, y un `codes.csv` con todos.
   - **Si el plan se ejecutará en otra sesión o lo correrá otra persona**, copia `redeem_codes.py` junto a los archivos generados y referencia esa copia. La ruta de la skill no existe fuera de este entorno.
   - **Inyección del ID:** el ID del descuento no va en los lotes. Si la herramienta de ejecución acepta un solo archivo de variables, prepara un archivo por lote con `discountId` incluido.
3. Crea **un** descuento de código con el primer código (la semilla) y toda la configuración. Los demás códigos se añaden en el paso siguiente.
4. Añade cada lote:

```graphql
mutation($discountId: ID!, $codes: [DiscountRedeemCodeInput!]!) {
  discountRedeemCodeBulkAdd(discountId: $discountId, codes: $codes) {
    bulkCreation { id }
    userErrors { field code message }
  }
}
```

5. Sondea cada `bulkCreation` hasta `done: true`:

```graphql
query($id: ID!) {
  discountRedeemCodeBulkCreation(id: $id) {
    done codesCount importedCount failedCount
    codes(first: 250) { nodes { code errors { field code message } } }
  }
}
```

6. Si `failedCount > 0`, lista los códigos fallidos y su error (normalmente `TAKEN`, porque el código ya existe en la tienda). Regenera solo esos y reintenta.
7. Reporta el total importado frente al solicitado y entrega `codes.csv` con los códigos válidos.

Un `bulkAdd` sin `userErrors` **no** significa que los códigos se crearon. Solo lo confirma el sondeo.

**Eliminar códigos de un descuento sin borrar el descuento:**
- Usa `discountCodeRedeemCodeBulkDelete(discountId:, ids: [...] | search: "...")`.
- Los IDs tienen la forma `gid://shopify/DiscountRedeemCode/…`.

## Respaldo antes de eliminar

Las eliminaciones no se pueden deshacer y Shopify no guarda copia. Antes de cualquier `*Delete` o `*BulkDelete`, exporta:

- la configuración completa de cada descuento a borrar;
- sus códigos de canje;
- sus métricas: `asyncUsageCount` y `totalSales`.

Con eso se puede recrear un descuento y conservar el historial para reportes.

**Pocos descuentos (cientos):** guarda en `respaldo-<fecha>.json` el resultado de la consulta paginada de arriba, añadiendo `codes(first: 250) { nodes { code asyncUsageCount } }` a los tipos de código.

**Muchos descuentos o códigos:** usa una operación masiva, que no consume el límite de tasa y devuelve un JSONL descargable.

```graphql
mutation {
  bulkOperationRunQuery(query: """
    {
      discountNodes {
        edges { node { id discount { __typename
          ... on DiscountCodeBasic { title status startsAt endsAt asyncUsageCount
            codes { edges { node { code asyncUsageCount } } } }
          ... on DiscountCodeBxgy { title status startsAt endsAt asyncUsageCount }
          ... on DiscountCodeFreeShipping { title status startsAt endsAt asyncUsageCount }
          ... on DiscountCodeApp { title status startsAt endsAt }
          ... on DiscountAutomaticBasic { title status startsAt endsAt asyncUsageCount }
          ... on DiscountAutomaticBxgy { title status startsAt endsAt }
          ... on DiscountAutomaticFreeShipping { title status startsAt endsAt }
          ... on DiscountAutomaticApp { title status startsAt endsAt }
        } } }
      }
    }
  """) {
    bulkOperation { id status }
    userErrors { field message }
  }
}
```

Después:
1. Sondea `currentBulkOperation { id status objectCount url }` hasta `COMPLETED`.
2. Descarga `url`.

En ese JSONL, las conexiones anidadas (códigos) llegan como líneas separadas con `__parentId`.

Amplía los fragmentos con los campos que haga falta recrear: `customerGets`, `context`, `minimumRequirement` y `combinesWith`. No borres nada hasta confirmar que el archivo existe y contiene los IDs que se van a eliminar.

## Activar, desactivar y eliminar en lote

| Mutación | Para |
|---|---|
| `discountCodeBulkActivate` | códigos |
| `discountCodeBulkDeactivate` | códigos |
| `discountCodeBulkDelete` | códigos (irreversible) |
| `discountAutomaticBulkDelete` | automáticos (irreversible) |

No existe activación o desactivación masiva de automáticos. Recórrelos uno a uno con `discountAutomaticActivate` / `Deactivate`.

Cada mutación acepta **exactamente uno** de `ids`, `search` o `savedSearchId`; pasar más de uno da `TOO_MANY_ARGUMENTS`. Devuelven `job { id done }`. Sondea con `job(id:) { done }` y después verifica con una consulta.

Protocolo cuando se usa `search`:
1. Ejecuta `discountNodes(query: <misma búsqueda>)` y `discountNodesCount`.
2. Muestra el conteo y una muestra de títulos.
3. Pide confirmación.
4. Ejecuta con `ids` explícitos de lo que se mostró; es más seguro que `search` porque la búsqueda puede cambiar entre la vista previa y la ejecución.

```graphql
mutation($ids: [ID!]) {
  discountCodeBulkDeactivate(ids: $ids) { job { id done } userErrors { field code message } }
}
```
