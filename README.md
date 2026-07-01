# ebird2CBRO

`ebird2CBRO` é um pacote que converte listas do eBird em colunas de presença/ausência na lista de espécies do Comitê Brasileiro de Registros Ornitológicos (CBRO)

## Ideia Principal

O pacote recebe uma lista de espécies do eBird vinda de:

- um checklist pessoal;
- um hotspot;
- uma planilha exportada de uma lista.

E então ele relaciona com a lista do CBRO e adiciona uma coluna marcando presença ou ausência

## Uso básico

```python
from ebird2cbro import ebird2cbro

df = ebird2cbro(
    source="S123456789",
    source_type="checklist",
    column_name="my_checklist",
    api_key="YOUR_EBIRD_API_KEY"
)