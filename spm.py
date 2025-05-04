import streamlit as st
import datetime
import locale
from carguetablas import cargar_tabla, calcular_a, calcular_A, calcular_spm_final, calcular_pension, formato_colombiano
from dateutil.relativedelta import relativedelta

# ✅ Establecer formato local (para puntos y comas como en Colombia)
locale.setlocale(locale.LC_ALL, '')

st.set_page_config(page_title="Cálculo SPM - Orlando Munar", layout="wide")

# 🟢 Título centrado
st.markdown("<h1 style='text-align: center;'>🧮 Cálculo de Ahorro Necesario - Pensión </h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Orlando Munar</h4>", unsafe_allow_html=True)
st.markdown("---")

# 🟩 Sección de parámetros del cálculo (izquierda)
col_param, col_data = st.columns([1, 2])

with col_param:
    st.markdown("### ⚙️ Parámetros del cálculo")

    # Selección de la operación a realizar
    operacion = st.selectbox("Seleccione la operación", ["Calcular SPM", "Calcular Pensión"])

    if operacion == "Calcular SPM":
        # Salario editable con validación visual y numérica
        salario_input = st.text_input("💰 Pensión", value="1.423.500")
        try:
            salario_minimo = int(salario_input.replace(".", "").replace(",", ""))
        except ValueError:
            st.error("💡 Formato inválido. Usa puntos como separador de miles: 1.423.500")
            salario_minimo = 0
    else:
        # SPM editable con validación visual y numérica
        spm_input = st.text_input("💰 SPM", value="100.000.000")
        try:
            spm = int(spm_input.replace(".", "").replace(",", ""))
        except ValueError:
            st.error("💡 Formato inválido. Usa puntos como separador de miles: 100.000.000")
            spm = 0

    # Interés técnico con validación de coma obligatoria
    interes_tecnico_input = st.text_input("📉 Tasa de interés técnico (anual, %)", value="3,81")
    if "." in interes_tecnico_input:
        st.error("🚫 Usa coma (,) como separador decimal, no punto.")
        interes_tecnico = 0.0
    else:
        try:
            interes_tecnico = float(interes_tecnico_input.replace(",", ".")) / 100
        except ValueError:
            st.error("💡 Ingresa un número válido. Ejemplo: 3,81")
            interes_tecnico = 0.0

    # Inflación calculada automáticamente según Decreto 3099 de 2015
    f_a1 = 5.20 / 100  # Inflación año 2024
    f_a2 = 9.28 / 100  # Inflación año 2023
    f_a3 = 13.12 / 100 # Inflación año 2022

    inflacion = (3 * f_a1 + 2 * f_a2 + f_a3) / 6

    st.markdown("### 📈 Inflación promedio (Decreto 3099 de 2015):")
    st.markdown(f"""
    - Inflación año 2024 (fₐ₋₁): **{f_a1*100:.2f}%**
    - Inflación año 2023 (fₐ₋₂): **{f_a2*100:.2f}%**
    - Inflación año 2022 (fₐ₋₃): **{f_a3*100:.2f}%**
    - 📌 Inflación usada para el cálculo (`f`): **{inflacion*100:.2f}%**
    """)

    # Selección de la fecha de inicio de pensión
    fecha_inicio_pension = st.date_input("📅 Fecha de inicio de pensión", value=datetime.date.today(), format="DD/MM/YYYY")

    # Obtener el mes (m) a partir de la fecha seleccionada
    m = fecha_inicio_pension.month
    # Cálculos derivados
    n = 13 - m if m > 1 else 0
    r = 7 - m if m < 7 else 0
    k_estrella = 0 if m == 1 else inflacion

    st.markdown(f"📌 Fecha de inicio de pensión seleccionada: **{fecha_inicio_pension.strftime('%d/%m/%Y')}**")
    st.markdown(f"📌 Mes de inicio: **{m} ({fecha_inicio_pension.strftime('%B').capitalize()})**")
    st.markdown(f"📌 n = {n} | r = {r} | K* = {k_estrella:.4f}")

# 🟪 Sección de datos del afiliado y sustituto
with col_data:
    st.markdown("### 👥 Información del afiliado y su sustituto")
    col1, col2 = st.columns(2)

    # 🔹 Afiliado
    with col1:
        st.markdown("#### 👤 Afiliado")
        genero_afiliado = st.selectbox("Género", ["Hombre", "Mujer"], key="genero_afiliado")
        fecha_nac_afiliado = st.date_input("Fecha de nacimiento", value=datetime.date(1963, 4, 15),
                                   min_value=datetime.date(1900, 1, 1),
                                   max_value=datetime.date.today(),
                                   key="fecha_nac_afiliado", format="DD/MM/YYYY")
        estado_afiliado = st.selectbox("Condición", ["Válido", "Inválido"], key="estado_afiliado")

        # 📅 Cálculo de edad fraccionada al inicio de pensión (similar a FRAC.AÑO en Excel)
        def calcular_frac_anio(fecha_nacimiento, fecha_referencia):
            delta = relativedelta(fecha_referencia, fecha_nacimiento)
            return delta.years + delta.months / 12 + delta.days / 365.25

        edad_afiliado = calcular_frac_anio(fecha_nac_afiliado, fecha_inicio_pension)
        edad_afiliado_entera = int(edad_afiliado)
        edad_afiliado = edad_afiliado_entera

        st.markdown(f"📅 Edad del afiliado: **{edad_afiliado} años**")
        tipo_afiliado = f"{genero_afiliado}_{'No_Invalido' if estado_afiliado == 'Válido' else 'Invalido'}"
        st.markdown(f"🧾 Tipo actuarial: **{tipo_afiliado}**")

    # 🔸 Sustituto
    with col2:
        st.markdown("#### 👥 Sustituto")

        tiene_conyuge = st.radio("¿Tiene sustituto?", ["Sí", "No"], horizontal=True) == "Sí"

        if tiene_conyuge:
            genero_conyuge = st.selectbox("Género", ["Hombre", "Mujer"], key="genero_conyuge")

            fecha_nac_conyuge = st.date_input("Fecha de nacimiento", value=datetime.date(1965, 9, 10),
                                              min_value=datetime.date(1900, 1, 1),
                                              max_value=datetime.date.today(),
                                              key="fecha_nac_conyuge", format="DD/MM/YYYY")

            estado_conyuge = st.selectbox("Condición", ["Válido", "Inválido"], key="estado_conyuge")

            edad_conyuge = calcular_frac_anio(fecha_nac_conyuge, fecha_inicio_pension)
            edad_conyuge_entera = int(edad_conyuge)
            edad_conyuge = edad_conyuge_entera

            tipo_conyuge = f"{genero_conyuge}_{'No_Invalido' if estado_conyuge == 'Válido' else 'Invalido'}"
            st.markdown(f"🧾 Tipo actuarial: **{tipo_conyuge}**")
            st.markdown(f"📅 Edad  del Beneficiario: **{edad_conyuge} años**")
        else:
            tipo_conyuge = None
            edad_conyuge = None

if st.button("📊 Calcular"):
    # 1. Calcular v
    v = 1 / (1 + interes_tecnico)

    # 2. Verificar si hay sustituto
    tiene_conyuge = tipo_conyuge is not None and edad_conyuge is not None

    # 3. Cargar tablas desde Excel
    tabla_afiliado = cargar_tabla("InsumoTablasSPM.xlsx", tipo_afiliado)
    tabla_sustituto = cargar_tabla("InsumoTablasSPM.xlsx", tipo_conyuge) if tiene_conyuge else None

    # 4. Calcular valor actuarial 'a'
    resultado_a = calcular_a(tabla_afiliado, edad_afiliado, v,
                             tabla_sustituto, edad_conyuge if tiene_conyuge else None)

    # 5. Calcular valor actuarial de seguro de vida entera (A)
    resultado_A = calcular_A(tabla_afiliado, edad_afiliado, v)

    # 6. Verificación de errores
    if "error" in resultado_a:
        st.error(f"❌ Error al calcular a: {resultado_a['error']}")
    elif "error" in resultado_A:
        st.error(f"❌ Error al calcular A: {resultado_A['error']}")
    else:
        st.success("✅ Cálculos actuariales realizados correctamente.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📘 Valor actuarial `a` (renta vitalicia conjunta):")
            st.markdown("- `a_x`: afiliado vivo")
            st.markdown("- `a_y`: sustituto vivo")
            st.markdown("- `a_xy`: ambos vivos")
            st.markdown("- `a_total = a_x + a_y - a_xy`")
            st.dataframe({
                "Componente": ["a_x (afiliado)", "a_y (sustituto)", "a_xy (ambos)", "a_total (renta conjunta)"],
                "Valor": [
                   formato_colombiano(resultado_a["a_x"], 5),
                    formato_colombiano(resultado_a["a_y"], 5),
                    formato_colombiano(resultado_a["a_xy"], 5),
                    formato_colombiano(resultado_a["a_total"], 5)
                ]
            })

        with col2:
            st.markdown("### 📘 Valor actuarial `A` (seguro de vida entera):")
            st.markdown("- Calculado como:  \n"
                        "  \\( A = \\frac{1}{l_x} \\sum v^{k+1}(l_{x+k} - l_{x+k+1}) \\)")
            st.dataframe({
                "Descripción": ["A_x (seguro de vida entera afiliado)"],
                "Valor": [round(resultado_A["A_x"], 8)]
            })

        if operacion == "Calcular SPM":
            # 7. Calcular el SPM final
            resultado_spm = calcular_spm_final(
                SMMLV=salario_minimo,
                a=resultado_a["a_total"],
                A=resultado_A["A_x"],
                v=v,
                K=inflacion,
                m=m,
                n=n,
                r=r
            )

            # 8. Mostrar resultado final del SPM
            st.markdown("### 💰 Resultado final del SPM:")
            st.markdown("- Basado en fórmula oficial del Decreto 1875 de 1997")
            st.dataframe({
        "Componente": [
            "SPM (saldo final requerido)",
            "Base actuarial [(12*f12 + 2*f2)*a + 6 + A]",
            "AuxilioFunerario",
            "f12 (ajuste por 12 mesadas mensuales)",
            "f2 (ajuste por 2 primas anuales adicionales)",
            "K* (inflación ajustada)",
            "U (factor descuento mensual)",
            "C (ajuste por mes inicial)"
        ],
        "Valor": [
            formato_colombiano(resultado_spm['SPM']),
            formato_colombiano(resultado_spm["base_valor"], 8),
            formato_colombiano(resultado_spm["AuxilioFunerario"], 8),
            formato_colombiano(resultado_spm["f12"], 8),
            formato_colombiano(resultado_spm["f2"], 8),
            formato_colombiano(resultado_spm["K*"], 4),
            formato_colombiano(resultado_spm["U"], 8),
            formato_colombiano(resultado_spm["C"], 8)
        ]
    })

            # 9. Interpretación dinámica (aquí sí ya puedes usar resultado_spm)
            mes_inicio_nombre = datetime.date(2025, m, 1).strftime('%B').capitalize()

            if m < 7:
                interpretacion_r = f"Como el primer pago de pensión se inicia en el mes {m} ({mes_inicio_nombre}), que es **antes de julio**, el valor de **r = {r}** se utiliza para ajustar los pagos cuatrimestrales que deben hacerse entre el mes de inicio y junio."
            else:
                interpretacion_r = f"Como el primer pago de pensión se inicia en el mes {m} ({mes_inicio_nombre}), que es **julio o posterior**, **no se aplica el parámetro r**, y su valor es **{r}**."

            descripcion = f"""
            - El saldo de pensión mínima (SPM) calculado es **{f"${resultado_spm['SPM']:,.2f}".replace(",", ".").replace(".", ",", 1)}**,
              lo que representa el **valor único que debe existir en la cuenta del afiliado** para garantizar una pensión mínima vitalicia.

            - El pago se proyecta para iniciar en el mes de **{mes_inicio_nombre}** (mes calendario número **{m}**).

            - El parámetro **n = {n}** se utiliza para ajustar el factor de descuento compuesto \( U^n \), y corresponde al número de meses hasta que se complete el año si el primer pago **no ocurre en enero**.

            - {interpretacion_r}

            - Se aplica un factor **C = {round(resultado_spm['C'], 4)}** como componente de ajuste, únicamente si el pago **no inicia en enero** (es decir, cuando \( m > 1 \)).

            - Este saldo considera una renta vitalicia pagadera mensualmente mientras vivan el afiliado y, si aplica, el sustituto (cónyuge), ajustada por inflación y descontada con la tasa técnica indicada.

            - **La fórmula usada se deriva del Artículo 1° del Decreto 1875 de 1997**, garantizando que los valores actuariales respeten las condiciones de supervivencia y las tablas de mortalidad correspondientes.
            """

            st.markdown("### 📄 Interpretación del resultado:")
            st.markdown(descripcion)

        else:
            # Calcular la pensión a partir del SPM ingresado
            resultado_pension = calcular_pension(
                SPM=spm,
                a=resultado_a["a_total"],
                A=resultado_A["A_x"],
                v=v,
                K=inflacion,
                m=m,
                n=n,
                r=r
            )

            # Mostrar resultado final de la pensión
            st.markdown("### 💰 Resultado final de la Pensión:")
            st.markdown("- Basado en fórmula oficial del Decreto 1875 de 1997")
            st.dataframe({
                "Componente": [
                    "Pensión (monto mensual)",
                    "Base actuarial [(12*f12 + 2*f2)*a + 6 + A]",
                    "AuxilioFunerario",
                    "f12 (ajuste por 12 mesadas mensuales)",
                    "f2 (ajuste por 2 primas anuales adicionales)",
                    "K* (inflación ajustada)",
                    "U (factor descuento mensual)",
                    "C (ajuste por mes inicial)"
                ],
                "Valor": [
                    formato_colombiano(resultado_pension['Pension']),
                    formato_colombiano(resultado_pension["base_valor"], 8),
                    formato_colombiano(resultado_pension["AuxilioFunerario"], 8),
                    formato_colombiano(resultado_pension["f12"], 8),
                    formato_colombiano(resultado_pension["f2"], 8),
                    formato_colombiano(resultado_pension["K*"], 4),
                    formato_colombiano(resultado_pension["U"], 8),
                    formato_colombiano(resultado_pension["C"], 8)
                ]
            })

            # Interpretación dinámica (aquí sí ya puedes usar resultado_pension)
            mes_inicio_nombre = datetime.date(2025, m, 1).strftime('%B').capitalize()

            if m < 7:
                interpretacion_r = f"Como el primer pago de pensión se inicia en el mes {m} ({mes_inicio_nombre}), que es **antes de julio**, el valor de **r = {r}** se utiliza para ajustar los pagos cuatrimestrales que deben hacerse entre el mes de inicio y junio."
            else:
                interpretacion_r = f"Como el primer pago de pensión se inicia en el mes {m} ({mes_inicio_nombre}), que es **julio o posterior**, **no se aplica el parámetro r**, y su valor es **{r}**."

            descripcion = f"""
            - La pensión calculada es **{f"${resultado_pension['Pension']:,.2f}".replace(",", ".").replace(".", ",", 1)}**,
              lo que representa el **monto mensual que se pagará al afiliado** para garantizar una pensión mínima vitalicia.

            - El pago se proyecta para iniciar en el mes de **{mes_inicio_nombre}** (mes calendario número **{m}**).

            - El parámetro **n = {n}** se utiliza para ajustar el factor de descuento compuesto \( U^n \), y corresponde al número de meses hasta que se complete el año si el primer pago **no ocurre en enero**.

            - {interpretacion_r}

            - Se aplica un factor **C = {round(resultado_pension['C'], 4)}** como componente de ajuste, únicamente si el pago **no inicia en enero** (es decir, cuando \( m > 1 \)).

            - Este monto considera una renta vitalicia pagadera mensualmente mientras vivan el afiliado y, si aplica, el sustituto (cónyuge), ajustada por inflación y descontada con la tasa técnica indicada.

            - **La fórmula usada se deriva del Artículo 1° del Decreto 1875 de 1997**, garantizando que los valores actuariales respeten las condiciones de supervivencia y las tablas de mortalidad correspondientes.
            """

            st.markdown("### 📄 Interpretación del resultado:")
            st.markdown(descripcion)
