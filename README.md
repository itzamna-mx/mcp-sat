# mcp-sat

[![PyPI version](https://img.shields.io/pypi/v/mcp-sat.svg)](https://pypi.org/project/mcp-sat/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Itzamná](https://img.shields.io/badge/Suite-Itzamn%C3%A1-7aa2f7.svg)](https://github.com/itzamna-mx)

Servidor [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) oficial y de código abierto para consultar y validar información tributaria del **SAT (Servicio de Administración Tributaria de México)** de forma **100% gratuita, sin tokens privados ni e.firma**.

Forma parte del ecosistema **[Itzamná](https://github.com/itzamna-mx)** para datos públicos y económicos de México.

---

## ⚡ Características principales

1. **Validación de CFDI en vivo (`consultar_cfdi`):**
   * Consulta directa al Web Service oficial del SAT (`ConsultaCFDIService.svc`).
   * Devuelve si la factura está **Vigente** o **Cancelada**, si es cancelable con/sin aceptación y alerta de **EFOS**.
   * **Cero costo y sin registro:** Utiliza el mismo servicio público que leen los códigos QR de las facturas.
2. **Listas negras del Artículo 69-B del CFF (`buscar_lista_negra` y `buscar_proveedor_lista_negra`):**
   * Detección inmediata de empresas fantasma / factureras (EFOS).
   * Clasificación oficial: *Presunto*, *Definitivo*, *Desvirtuado* o *Sentencia Favorable*.
   * Base de datos SQLite local ultrarrápida (<1 ms por consulta) con sincronización directa desde el portal del SAT.
3. **Validación de RFC (`validar_rfc`):**
   * Validación sintáctica de personas físicas y morales.
   * Cálculo del **dígito verificador oficial** según el algoritmo matemático del SAT.
   * Manejo de RFCs genéricos oficiales (`XAXX010101000` y `XEXX010101000`).

---

## 🛠️ Herramientas MCP expuestas

| Herramienta | Argumentos | Descripción |
| :--- | :--- | :--- |
| **`consultar_cfdi`** | `rfc_emisor`, `rfc_receptor`, `total`, `uuid` | Consulta en vivo el estatus oficial de una factura en el SAT. |
| **`buscar_lista_negra`** | `rfc` | Comprueba si un RFC aparece en el listado de EFOS del Art. 69-B. |
| **`buscar_proveedor_lista_negra`** | `razon_social`, `limite` | Busca proveedores por coincidencia en su nombre o razón social en la lista 69-B. |
| **`validar_rfc`** | `rfc` | Valida estructura, tipo de persona, fecha y dígito verificador. |
| **`actualizar_lista_sat`** | *(ninguno)* | Descarga e indexa en la base SQLite local el archivo oficial de listas 69-B del SAT. |

---

## 🚀 Instalación y Uso

### Con `uvx` (recomendado, sin instalación previa)

```bash
uvx mcp-sat
```

### Con `pip`

```bash
pip install mcp-sat
mcp-sat
```

---

## ⚙️ Configuración en Clientes MCP

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "sat": {
      "command": "uvx",
      "args": ["mcp-sat"]
    }
  }
}
```

### Cursor / Antigravity / Gemini CLI

```json
{
  "mcpServers": {
    "sat": {
      "command": "mcp-sat",
      "args": []
    }
  }
}
```

---

## 💻 Comandos de Consola (CLI)

El paquete incluye herramientas de diagnóstico directo en tu terminal:

```bash
# Probar conexión en vivo con el Web Service del SAT
mcp-sat --test

# Descargar o actualizar la lista negra del Art. 69-B (14,000+ registros)
mcp-sat --actualizar-listas

# Ver información de la base de datos local
mcp-sat --info

# Ejecutar como servicio HTTP / SSE
mcp-sat --transport streamable-http --port 8000
```

---

## 🏛️ Sobre Itzamná

Este servidor forma parte de **[Itzamná](https://github.com/itzamna-mx)**, una iniciativa independiente y abierta para dotar a los agentes de Inteligencia Artificial de acceso estructurado a los datos públicos y oficiales de México:

* [`mcp-banxico`](https://github.com/itzamna-mx/mcp-banxico): Indicadores económicos, tipo de cambio FIX y tasas.
* [`mcp-inegi`](https://github.com/itzamna-mx/mcp-inegi): Indicadores económicos, inflación y catálogo municipal.
* [`mcp-sat`](https://github.com/itzamna-mx/mcp-sat): Validación fiscal, facturación y listas de EFOS.

*Nota: Este es un proyecto comunitario de código abierto y no tiene afiliación oficial con el Servicio de Administración Tributaria (SAT).*

---

## 📄 Licencia

Licencia [MIT](LICENSE) © 2026 Iñaki Sobera.
