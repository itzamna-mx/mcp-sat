# Notas de Integración con los Servicios Públicos del SAT

Documento de referencia técnica sobre las particularidades, trampas y consideraciones al consultar las fuentes públicas del SAT.

---

## 1. Web Service de Validación de CFDI (`ConsultaCFDIService.svc`)

* **Endpoint:** `https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc`
* **SOAPAction:** `http://tempuri.org/IConsultaCFDIService/Consulta`
* **Método:** POST con sobre SOAP 1.1 y envoltorio `<![CDATA[ ... ]]>`.
* **Cero autenticación:** No requiere usuario, contraseña, token, ni certificado digital. Es el mismo servicio que valida los códigos QR impresos en facturas.

### Trampas y consideraciones:
1. **Formato exacto de la expresión impresa:**
   * La cadena enviada en el CDATA tiene la forma: `?re=RFC_EMISOR&rr=RFC_RECEPTOR&tt=TOTAL&id=UUID`.
   * El parámetro `&tt=` debe coincidir con el total del CFDI registrado en el SAT.
   * Si el importe difiere en decimales o formato, el SAT devuelve `N - 602: Comprobante no encontrado`.
2. **ValidacionEFOS:**
   * La respuesta XML incluye la etiqueta `<a:ValidacionEFOS>`.
   * Valor `200`: El RFC emisor no tiene coincidencias en la lista de EFOS del SAT al momento de la consulta.
   * Valor `100`: El emisor presenta alguna presunción o estatus en listas negras.

---

## 2. Listado de Contribuyentes con Operaciones Inexistentes (Artículo 69-B del CFF)

* **URL oficial:** `http://omawww.sat.gob.mx/cifras_sat/Documents/Listado_Completo_69-B.csv`
* **Frecuencia:** Actualizado periódicamente por el SAT en el portal oficial y en el Diario Oficial de la Federación (DOF).

### Trampas y consideraciones:
1. **Codificación:** El archivo CSV no está en UTF-8, sino en **Latin-1 / ISO-8859-1 (Windows-1252)**. Intentar parsearlo directamente con `utf-8` lanza un `UnicodeDecodeError`.
2. **Encabezado variable:** Las primeras 2 a 3 líneas del archivo contienen notas informativas legales antes de la fila de cabeceras de columnas (`No,RFC,Nombre del Contribuyente...`). El parser debe buscar dinámicamente el inicio de las columnas o filas de datos.
3. **Optimización con SQLite:** Al tener ~14,000 registros y pesar más de 4.5 MB, consultarlo en memoria o en texto plano en cada llamada es lento. `mcp-sat` lo convierte a una base de datos SQLite local indexada por RFC y por razón social, reduciendo el tiempo de consulta a **menos de 1 milisegundo**.

---

## 3. Algoritmo de Dígito Verificador del RFC

* El cálculo utiliza una tabla de ponderaciones donde cada carácter se mapea a un valor numérico (0-9 -> 0-9, A-Z -> 10-35, espacio/& -> valores fijos).
* **Persona Moral (12 caracteres):** Debe anteponerse un espacio en blanco (` `) para alinear las posiciones a los 12 pesos matemáticos `(14 - i)`.
* **RFCs Genéricos:** `XAXX010101000` (Público en general) y `XEXX010101000` (Extranjeros) son excepciones oficiales válidas por regla fiscal.
