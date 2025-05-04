import pandas as pd

MAX_EDAD = 110  # límite razonable para actuarial

def cargar_tabla(filepath, hoja):
    return pd.read_excel(filepath, sheet_name=hoja)

def get_lx(tabla, edad):
    fila = tabla[tabla['x'] == edad]
    if not fila.empty:
        lx_valor = float(str(fila.iloc[0]['lx']).replace(".", "").replace(",", "."))
        print(f"[DEBUG] lx para edad {edad}: {lx_valor}")  # 🔍 Depuración en consola
        return lx_valor
    else:
        #print(f"[DEBUG] Edad {edad} no encontrada en la tabla lx.")  # ⚠️ Si no encuentra
        return 0.0


def calcular_a(tabla_afiliado, edad_afiliado, v, tabla_conyuge=None, edad_conyuge=None):
    lx_a = get_lx(tabla_afiliado, edad_afiliado)
    if lx_a == 0:
        return {"error": f"Edad {edad_afiliado} no encontrada para afiliado."}

    suma1 = sum([
        get_lx(tabla_afiliado, edad_afiliado + k) * (v ** k)
        for k in range(1, MAX_EDAD - edad_afiliado)
        if get_lx(tabla_afiliado, edad_afiliado + k) > 0
    ])
    parte1 = suma1 / lx_a

    parte2 = 0
    parte3 = 0

    if tabla_conyuge is not None and edad_conyuge is not None:
        lx_b = get_lx(tabla_conyuge, edad_conyuge)
        if lx_b == 0:
            return {"error": f"Edad {edad_conyuge} no encontrada para sustituto."}

        suma2 = sum([
            get_lx(tabla_conyuge, edad_conyuge + k) * (v ** k)
            for k in range(1, MAX_EDAD - edad_conyuge)
            if get_lx(tabla_conyuge, edad_conyuge + k) > 0
        ])
        parte2 = suma2 / lx_b

        suma3 = sum([
            get_lx(tabla_afiliado, edad_afiliado + k) *
            get_lx(tabla_conyuge, edad_conyuge + k) * (v ** k)
            for k in range(1, min(MAX_EDAD - edad_afiliado, MAX_EDAD - edad_conyuge))
            if get_lx(tabla_afiliado, edad_afiliado + k) > 0 and get_lx(tabla_conyuge, edad_conyuge + k) > 0
        ])
        parte3 = suma3 / (lx_a * lx_b)

    a_total = parte1 + parte2 - parte3
    return {
        "lx_afiliado": lx_a,
        "lx_sustituto": get_lx(tabla_conyuge, edad_conyuge) if tabla_conyuge is not None else None,
        "a_x": parte1,
        "a_y": parte2,
        "a_xy": parte3,
        "a_total": a_total
    }




def calcular_A(tabla_afiliado, edad_afiliado, v):
    lx_a = get_lx(tabla_afiliado, edad_afiliado)
    if lx_a == 0:
        return {"error": f"Edad {edad_afiliado} no encontrada para afiliado."}

    suma = 0
    for k in range(0, MAX_EDAD - edad_afiliado - 1):
        lx_k = get_lx(tabla_afiliado, edad_afiliado + k)
        lx_k1 = get_lx(tabla_afiliado, edad_afiliado + k + 1)
        if lx_k == 0 or lx_k1 == 0:
            break
        termino = (v ** (k + 1)) * (lx_k - lx_k1)
        suma += termino

    A = suma / lx_a
    return {
        "A_x": A
    }



def calcular_spm_final(SMMLV, a, A, v, K, m, n, r):
    K_estrella = 0 if m == 1 else K

    # Cálculo de U
    U = (v / (1 + K)) ** (1 / 12)

    # Cálculo de f12 y f2
    if K != 0:
            f12 = ((1 + 11*K/24))/ (1+ K)
            f2 = (1 +(K/4)) / (1+K)
    else:
            f12 = 1 / 12
            f2 = 1 / 2


    # Cálculo de C según el mes
    if m == 1:
        C = 0
    elif 1 < m <= 6:
        C = ((U - U ** (n + 1)) / (1 - U)) + (U ** r ) + U ** n
    else:  # m > 6
        C = ((U - U ** (n + 1)) / (1 - U)) + U ** n

    
    
    SMMLV2 = 1423500  # Valor fijo para referencia normativa
    P = SMMLV  # Este es el valor imputado por el usuario

    # Ajuste según la pensión deseada
    if P < 5 * SMMLV2:
        factor_A = 5
    elif 5 * SMMLV2 <= P <= 10 * SMMLV2:
        factor_A = 1
    else:  # P > 10 * SMMLV2
        factor_A = 10

    A_modificado = factor_A * A

    # Cálculo del SPM base con A ajustado
    base = (12 * f12 + 2 * f2) * a + 6 + A_modificado
    
    #cambiamos 1.05 por 1.02
    spm = 1.02 * SMMLV * (((12 * f12 + 2 * f2) * a + 6 + A_modificado)*(1 + K_estrella) * (U ** n) + C)

    return {
        "SPM": spm,
        "base_valor": base,
        "AuxilioFunerario":A_modificado,
        "f12": f12,
        "f2": f2,
        "K*": K_estrella,
        "U": U,
        "C": C
        
    }



def formato_colombiano(valor, decimales=2):
    if isinstance(valor, (int, float)):
        return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return valor


def calcular_pension(SPM, a, A, v, K, m, n, r):
    K_estrella = 0 if m == 1 else K

    # Cálculo de U
    U = (v / (1 + K)) ** (1 / 12)

    # Cálculo de f12 y f2
    if K != 0:
        f12 = ((1 + 11 * K / 24)) / (1 + K)
        f2 = (1 + (K / 4)) / (1 + K)
    else:
        f12 = 1 / 12
        f2 = 1 / 2

    # Cálculo de C según el mes
    if m == 1:
        C = 0
    elif 1 < m <= 6:
        C = ((U - U ** (n + 1)) / (1 - U)) + (U ** r) + U ** n
    else:  # m > 6
        C = ((U - U ** (n + 1)) / (1 - U)) + U ** n

    SMMLV2 = 1423500  # Valor fijo para referencia normativa

    # Cálculo inicial de la pensión
    P_inicial = SPM / (1.02 * (((12 * f12 + 2 * f2) * a + 6 + A) * (1 + K_estrella) * (U ** n) + C))

    # Ajuste del auxilio funerario según la pensión inicial
    if P_inicial < 5 * SMMLV2:
        factor_A = 5
    elif 5 * SMMLV2 <= P_inicial <= 10 * SMMLV2:
        factor_A = 1
    else:  # P_inicial > 10 * SMMLV2
        factor_A = 10

    A_modificado = factor_A * A

    # Cálculo final de la pensión con A ajustado
    base = (12 * f12 + 2 * f2) * a + 6 + A_modificado
    Pension = SPM / (1.02 * (base * (1 + K_estrella) * (U ** n) + C))

    return {
        "Pension": Pension,
        "base_valor": base,
        "AuxilioFunerario": A_modificado,
        "f12": f12,
        "f2": f2,
        "K*": K_estrella,
        "U": U,
        "C": C
    }
