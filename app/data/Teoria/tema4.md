# TEMA 4: Diseño iterativo y noción de secuencia

## 4.1 Tratamiento secuencial

### Definición de secuencia
*   **Secuencia:** Conjunto de valores de cualquier tipo. Es significativo el orden entre ellos:
    *   `Secu1 = [32, 64, 85]`
    *   `Secu2 = ['h', 'o', 'l', 'a']`
    *   `Secu3 = [ ]`
*   **Longitud de una secuencia (`long`):** Es el número de elementos que la componen:
    *   `S = S1 S2 S3 ... Sn`  ->  `long(S) = n`
    *   La longitud de una secuencia no se conoce a priori.
    *   `long(Secu1) = 3`, `long(Secu2) = 4`, `long(Secu3) = 0`
*   **Existe una relación de orden:** `[32, 64, 85] != [85, 64, 32]`

### Definición de una máquina secuencial

Una secuencia se puede visualizar como una cinta, y el acceso a ella como una ventana que nos muestra un único elemento cada vez:

```text
                  Ventana
                    EA
                    v
Cinta:[ L | a | v | i | d | a | e | s | u | n | a | # ]
       <--------->     <----------------------------->
         Parte iz.                Parte der.
```
*La ventana señala el Elemento Actual (EA).*

### Primitivas para el primer modelo de acceso secuencial

**Acceso Secuencial:**
*   `Comenzar(S)`: Inicia una consulta sobre una secuencia S y su primer elemento es el elemento actual.
*   `Avanzar(S)`: Avanza al siguiente elemento de S.
*   `EA(S)`: Retorna el elemento actual de S.

**Creación Secuencial:**
*   `Crear(S)`: Crea S como una secuencia vacía sobre la que podemos añadir elementos por la derecha.
*   `Registrar (S, e)`: Graba el elemento `e` como último elemento de una secuencia S.
*   `Marcar(S)`: Graba la marca de fin en la secuencia S.

#### Representación visual de las primitivas:
**Comenzar(S):** La ventana se sitúa en el primer elemento.
```text
         EA
         v
Cinta:[  L  | a | v | i | d | a | e | s | u | n | a | # ]
    <>       <----------------------------------------->
Parte iz.                    Parte der.
```

**Avanzar(S):** La ventana se desplaza a la derecha.
```text
             EA
             v
Cinta:[ L |  a  | v | i | d | a | e | s | u | n | a | # ]
       <->       <------------------------------------->
    Parte iz.                   Parte der.
```

**EA(S) = MarcaFin:** (Secuencia marcadas)
```text
                                                     EA
                                                     v
Cinta:[ L | a | v | i | d | a | e | s | u | n | a |  #  ]
       <----------------------------------------->       <>
                        Parte iz.                    Parte der.
```

**FDS (S) (Fin de Secuencia - Secuencia no marcadas):**
Devuelve FALSO si estamos sobre un elemento, y VERDADERO si la ventana ha sobrepasado el último elemento.
```text
Cinta:[ L | a | v | i | d | a | e | s | u | n | a |   ]
        ^                                           ^
        |                                           |
    EA(FALSO)                                 EA(VERDADERO)
```

#### Esquema de Creación vs Consulta
```text
CREACIÓN:                        | CONSULTA:
Crear          [ ]               | Comenzar   [ X | y | Z | # ]
                                 |              ^
                                 |              EA
Registrar('X') [ X ]             | Avanzar    [ X | y | Z | # ]
                                 |                  ^
                                 |                  EA
Registrar('y') [ X | y ]         | Avanzar    [ X | y | Z | # ]
                                 |                      ^
                                 |                      EA
Registrar('Z') [ X | y | Z ]     | Avanzar    [ X | y | Z | # ]
                                 |                          ^
                                 |                          EA
Marcar         [ X | y | Z | # ] | 
```

#### Operaciones permitidas en cada estado:

| | ninguno | creación | marcada | consulta |
| :--- | :---: | :---: | :---: | :---: |
| **Comenzar** | X | X | consulta | consulta |
| **Avanzar** | X | X | X | consulta |
| **EA** | X | X | X | consulta |
| **Crear** | creación | creación | creación | creación |
| **Registrar**| X | creación | X | X |
| **Marcar** | X | marcada | X | X |

### Análisis iterativo

**Composición secuencial:**
*   `e0 {PRE: de A1}` -> `A1` -> `e1 {POST: de A1, PRE: de A2}` -> `A2` -> `e2` ... `Am` -> `em {POST: de Am}`
*   El número `m` de estados intermedios es conocido y fijado en el diseño.
*   Las acciones que llevan de un estado al siguiente son distintas.

**Composición iterativa:**
*   `e0 {PRE: de A}` -> `A` -> `e1 {POST: de A, PRE: de A}` -> `A` -> `e2` ... `A` -> `en {POST: de A}`
*   El número `n` de estados intermedios es variable y, en general, desconocido a priori.
*   La acción que lleva de un estado al siguiente siempre es la misma.

Diseñaremos algoritmos iterativos modelando la iteración como el tratamiento de una secuencia. 

**CUESTIÓN:** Cualesquiera estados intermedios `e_k` y `e_k+1` son, al mismo tiempo, precondición y postcondición de la misma acción elemental A. Si son pre y postcondición de la misma acción, ¿significa que son el mismo estado? ¿El proceso iterativo no avanza?

**RESPUESTA:** Los estados intermedios **no** son el mismo, pero todos comparten una propiedad común que les hace ser pre y postcondición a la vez de A. 

Esta propiedad se llama **INVARIANTE**.

**Ejemplo: Determinar la longitud de un texto dado (S = "esto es un ejem#")**
Para determinar la longitud, ¿cuál es el tratamiento elemental a aplicar a cada elemento?
*   `e0`: EA = primero (S)  => `conta = 0` y `EA = 'e'`
*   `e1`: T aplicado sobre S1 y EA=S2 => `conta = 1` y `EA = 's'`
*   ...
*   `ek`: T aplicado sobre S1, S2,..., Sk y EA = Sk+1 => `conta = k` y `EA = 'e'` (`k = 13`)
*   ...
*   `en`: T aplicado sobre S y EA = MarcaFin => `conta = 15` y `EA = MarcaFin`

**INVARIANTE:** `cont = número de elementos de la parte izquierda de S`

En un esquema algorítmico iterativo hay que completar los fragmentos de código dependientes del problema: **inicialización** y **tratamiento elemental** en el cuerpo del bucle.
```pseudocode
Léxico
    conta : entero >=0;
    S : secuencia de caracteres;
Algoritmo
    Comenzar(S); conta <- 0; // Acciones de inicialización
    MIENTRAS EA(S) != MarcaFin HACER
        conta <- conta + 1; Avanzar(S) // Cuerpo
    FIN_MIENTRAS;
    Escribir(conta) // Finalización
Fin.
```

**¿Cómo obtenemos la inicialización?**
Para cada variable `v` debemos responder: ¿Cuál es la solución para una secuencia vacía? -> `v <- valor inicial`

**¿Cómo obtenemos el tratamiento elemental?**
Suponemos que conocemos la solución para la subsecuencia izquierda (elementos ya recorridos). Este valor es conocido (Hipótesis de inducción). ¿Qué tratamiento se debe realizar para tener ahora la solución sumando el elemento actual? -> `v_i <- g_i (v_i, EA)`

**Problema: cálculo del valor medio de notas**
*   **Especificación:** `PRE { S es secuencia de reales }`, `POST { i = Long(S) y suma = SUM(S_i), y numElem = Long(S) }`
*   **Inicialización:** `suma <- 0`, `numElem <- 0`
*   **Tratamiento elemental:** `suma <- suma + EA(S)`, `numElem <- numElem + 1`

```pseudocode
LÉXICO
    S : Secuencia de Real;
    suma : Real; // lleva cuenta de la suma total
    numElem : Entero; // cuenta el número de notas
ALGORITMO
    Comenzar(S); suma <- 0; numElem <- 0;
    MIENTRAS EA(S) != MarcaFin HACER
        suma <- suma + EA(S); numElem <- numElem + 1; 
        Avanzar(S)
    FIN_MIENTRAS;
    SI numElem > 0 ENTONCES
        Escribir("Valor medio de las notas: ", suma/numElem)
    SI_NO Escribir("Secuencia vacía")
    FIN_SI
FIN.
```

---

## 4.2 Esquemas algorítmicos de recorrido

**Esquema algorítmico:** plantilla de algoritmo aplicable no a un problema, sino a una *clase* de problemas.

**Recorrido, o enumeración secuencial:** Aplicación de un mismo tratamiento a *todos* los elementos de la colección. En cada caso debemos estudiar si podemos:

a) Tratar la secuencia vacía como el resto de secuencias (H1)

b) Tratar el primer elemento como al resto de elementos (H2)

Estudiaremos tres esquemas algorítmicos de recorrido para secuencias marcadas:
*   **Esquema 1:** Tratamiento integrado de la secuencia vacía y del primer elemento (H1 y H2).
*   **Esquema 2:** Tratamiento especial de la secuencia vacía y tratamiento integrado del primer elemento (¬H1 y H2).
*   **Esquema 3:** Tratamiento especial de la secuencia vacía y del primer elemento (¬H1 y ¬H2).

### Esquema 1: H1 y H2
```pseudocode
ESQUEMA ALGORÍTMICO:
    Comenzar;
    { Inicialización del tratamiento }
    MIENTRAS EA != MarcaFin HACER
        { Tratamiento de EA }
        Avanzar
    FIN_MIENTRAS;
    { Terminación del tratamiento }
```

### Esquema 2: ¬H1 y H2
```pseudocode
ESQUEMA ALGORÍTMICO:
    Comenzar;
    SEGÚN EA
        EA = MarcaFin :
            { Tratamiento sec. vacía }
        EA != MarcaFin :
            { Inic. del tratamiento }
            REPETIR
                { Tratamiento de EA }
                Avanzar
            HASTA EA = MarcaFin;
            { Terminación del tratto. }
    FIN_SEGÚN;
```

### Esquema 3: ¬H1 y ¬H2
```pseudocode
ESQUEMA ALGORÍTMICO:
    Comenzar;
    SEGÚN EA
        EA = MarcaFin :
            { Tratamiento sec. vacía }
        EA != MarcaFin :
            { Tratamiento 1er elemto. }
            ITERAR
                Avanzar
                DETENER EA = MarcaFin;
                { Tratamiento de EA }
            FIN_ITERAR;
            { Terminación del tratto. }
    FIN_SEGÚN;
```

### Problema: cálculo de la meseta mayor
Dada una secuencia de enteros > 0, llamamos meseta a una sucesión de valores idénticos. Diseñar un algoritmo que calcule la longitud de la meseta mayor.
Ejemplo: `S =[35, 18, 18, 18, 5, 62, 35, 35, 11, 11, 11, 11, 9, 9]`. La meseta mayor es 4 (valores 11).

**Análisis Suponiendo H2:**
*   `Post = { p = LongMesetaMayor (S) }`
*   `Inv = { p = LongMesetaMayor(Piz) y u = último(Piz) y m = LongUltMeseta(Piz) }`
*   Inicialización: `p <- 0; m <- 0; u <- ??` (¡no está definido para secuencia vacía!)
*   Tratamiento: `SI EA(S) != u ENTONCES m <- 1 SI_NO m <- m + 1`
*   Puesto que la secuencia es de positivos, podemos aplicar el esquema 1 si tomamos como último un valor `<= 0` (truco sucio).

**Solución con H2 (Esquema 1):**
```pseudocode
Léxico
    S : secuencia de Entero;
    p, m, u : Entero;
Algoritmo
    Comenzar(S);
    p <- 0; m <- 0; u <- 0;
    MIENTRAS EA(S) != MarcaFin HACER
        SI EA(S) = u ENTONCES
            m <- m + 1
        SI_NO
            m <- 1
        FIN_SI;
        SI m > p ENTONCES
            p <- m
        FIN_SI;
        u <- EA(S);
        Avanzar(S)
    FIN_MIENTRAS;
    Escribir(p)
FIN.
```

**Solución con ¬H2 (Esquema 3):**
```pseudocode
Algoritmo
    Comenzar(S);
    SEGÚN EA(S)
        EA(S) = MarcaFin :
            Escribir("Secuencia vacía");
        EA(S) != MarcaFin :
            p <- 1; m <- 1; u <- EA(S); 
            ITERAR
                Avanzar(S)
                DETENER EA(S) = MarcaFin;
                    SI EA(S) = u ENTONCES m <- m + 1
                    SI_NO m <- 1
                    FIN_SI;
                    SI m > p ENTONCES p <- m FIN_SI;
                    u <- EA(S)
            FIN_ITERAR;
            Escribir(p)
    FIN_SEGÚN
FIN.
```

### Problema: obtención del máximo
*   `Postcondición: m = max(S)`
*   `Invariante: m = max(Piz(S))`
*   `max` para la secuencia vacía = ?? (no definido: ¬H2)
*   Inicialización: `m <- EA(S);`
*   Cuerpo: `SI EA(S) > m ENTONCES m <- EA(S) FIN_SI;`
*   Terminación: `Escribir(m);`

```pseudocode
Léxico
    S : secuencia de Entero;
    m : entero; // el anterior
Algoritmo
    Comenzar(S);
    SEGÚN EA(S)
        EA(S) = MarcaFin :
            Escribir("Secuencia vacía");
        EA(S) != MarcaFin :
            m <- EA(S); 
            ITERAR
                Avanzar(S)
                DETENER EA(S) = MarcaFin;
                    SI EA(S) > m ENTONCES
                        m <- EA(S)
                    FIN_SI
            FIN_ITERAR;
            Escribir(m)
    FIN_SEGÚN
FIN.
```

### Problema: copia de una secuencia
A partir de una secuencia S1 deseamos crear otra secuencia S2 idéntica.
```pseudocode
Léxico
    S1, S2 : secuencia de Carácter;
Algoritmo
    Comenzar(S1);
    Crear(S2);
    // Inv : { Piz(S1) = Piz(S2) }
    MIENTRAS EA(S1) != MarcaFin HACER
        Registrar(S2, EA(S1));
        Avanzar(S1);
    FIN_MIENTRAS;
    Marcar(S2);
FIN.
```

### Problema: máximos y mínimos
Dada una secuencia de enteros S, obtener: valor máximo (`ma`), posición primera vez (`pma`), posición última vez (`uma`), número de veces (`nma`), y lo mismo para el mínimo (`mi`, `pmi`, `umi`, `nmi`).
Ejemplo: `S =[34, 1, 90, 39, 1, 15, 90, 25, 1, 10]` -> `ma = 90`, `pma = 3`, `uma = 7`, `nma = 2`...

Relaciones de dependencia topológica:
`pos` -> `pma`, `uma`, `nma`, `pmi`, `umi`, `nmi`, `ma`, `mi`

```text
           +--> pma --+
           |          |
           +--> uma --+--> ma
           |          |
           |    nma --+
pos -------|
           +--> pmi --+
           |          |
           +--> umi --+--> mi
                      |
                nmi --+
```

```pseudocode
Léxico
    S : secuencia de Entero;
    ma, nma, pma, uma : Entero;
    mi, nmi, pmi, umi, pos : Entero;
Algoritmo
    Comenzar(S);
    SEGÚN EA(S)
        EA(S) = MarcaFin :
            Escribir("Secuencia vacía");
        EA(S) != MarcaFin :
            ma <- EA(S); mi <- EA(S);
            nma <- 1; pma <- 1; uma <- 1; 
            nmi <- 1; pmi <- 1; umi <- 1;
            pos <- 1;
            ITERAR
                Avanzar(S);
                DETENER EA(S) = MarcaFin;
                pos <- pos + 1;
                
                SEGÚN EA(S), ma
                    EA(S) = ma : uma <- pos; nma <- nma + 1;
                    EA(S) > ma : uma <- pos; pma <- pos; ma <- EA(S); nma <- 1;
                    EA(S) < ma : ;
                FIN_SEGÚN;
                
                SEGÚN EA(S), mi
                    EA(S) = mi : umi <- pos; nmi <- nmi + 1;
                    EA(S) < mi : umi <- pos; pmi <- pos; mi <- EA(S); nmi <- 1;
                    EA(S) > mi : ;
                FIN_SEGÚN
            FIN_ITERAR;
            Escribir(ma, nma, pma, uma);
            Escribir(mi, nmi, pmi, umi)
    FIN_SEGÚN
FIN.
```

### Problema: intercalación de secuencias
Dadas dos secuencias S1 y S2 ordenadas decrecientemente, obtener R con los elementos conservando el orden.

**Ejemplo:** 
Si las secuencias de entrada son: `S1 = [25, 11, 11, 3, 1, 1]` y `S2 = [38, 25, 14, 11, 9, 9, 7]`. 

La secuencia resultado debería ser:
`R = [38, 25, 25, 14, 11, 11, 11, 9, 9, 7, 3, 1, 1]`

Debemos tener en cuenta:
*   **Postcondición**: Post : { R = Intercalar(S1, S2) }
*   **Invariante**: Inv : { Piz(R) = Intercalar(Piz(S1), Piz(S2)) }

Necesitamos una definición inductiva de la función *Intercalar*.
Los casos triviales son:
* `Intercalar ([], []) = []`
* `Intercalar (T·e,[]) = T·e`
* `Intercalar ([], T·e) = T·e`

**Análisis 1:** (punto de vista de lo ya tratado)
```pseudocode
Intercalar (T1·e1, T2·e2) =
    Intercalar (T1, T2) & [e1, e2]     si e1 = e2
    Intercalar (T1, T2·e2) & [e1]      si e1 < e2
    Intercalar (T1·e1, T2) & [e2]      si e1 > e2
```

**Análisis 2:** (punto de vista de lo pendiente de recorrer)
```pseudocode
Intercalar (e1 º T1, e2 º T2) =
    [e1, e2] & Intercalar (T1, T2)     si e1 = e2
    [e2] & Intercalar (e1 º T1, T2)    si e1 < e2
    [e1] & Intercalar (T1, e2 º T2)    si e1 > e2
```

Para los casos triviales definiremos una acción parametrizada que copie el resto de una secuencia en otra:

```pseudocode
CopiarResto : acción(dato-resultado S, R : secuencia de Entero);
Pre : { (Estado(S) = consulta) Y (Estado(R) = creación) Y
        (Pdr(S) = T·MarcaFin) Y (EA(S) != MarcaFin) Y (R = U) }
Post : { (EA(S) = MarcaFin) Y (R = U & T) }
Algoritmo
    REPETIR
        Registrar(R, EA(S));
        Avanzar(S)
    HASTA EA(S) = MarcaFin
FIN;
```

En los casos no triviales haremos un análisis de casos y registraremos en cada caso el mayor elemento.

```pseudocode
Léxico
    S1, S2, R : secuencia de Entero;
    CopiarResto : acción // definida antes

Algoritmo
    Comenzar(S1); Comenzar(S2); Crear(R);
    MIENTRAS (EA(S1) != MarcaFin) Y (EA(S2) != MarcaFin) HACER
        SEGÚN EA(S1), EA(S2)
            EA(S1) = EA(S2) :
                Registrar(R, EA(S1));
                Registrar(R, EA(S2));
                Avanzar(S1); Avanzar(S2);
            EA(S1) > EA(S2) :
                Registrar(R, EA(S1));
                Avanzar(S1);
            EA(S1) < EA(S2) :
                Registrar(R, EA(S2));
                Avanzar(S2);
        FIN_SEGÚN
    FIN_MIENTRAS;
    
    SEGÚN EA(S1), EA(S2)
        (EA(S1) != MarcaFin) Y (EA(S2) = MarcaFin) :
            CopiarResto(S1, R);
        (EA(S1) = MarcaFin) Y (EA(S2) != MarcaFin) :
            CopiarResto(S2, R);
        EN_OTRO_CASO : ;
    FIN_SEGÚN;
    Marcar(R)
FIN.
```

---

## 4.3 Esquemas algorítmicos de búsqueda

**Problema de la búsqueda:** Encontrar el primer elemento de la secuencia que cumpla una cierta propiedad `Pro`.
*   **Postcondición:** `Post = { (Pro(EA) = Verdadero O EA = MarcaFin) Y (ParaTodo e en Piz : Pro(e) = Falso) }`
*   **Invariante:** `Inv = { ParaTodo e en Piz : Pro(e) = Falso }` (Ningún elemento de la parte izquierda de S cumple la propiedad Pro).
*   **Condición de continuación:** `(EA != MarcaFin) Y NO Pro(EA)` (Continuará la iteración si no hemos llegado al final de la secuencia y tampoco hemos encontrado un elemento que cumpla la propiedad Pro).

### Esquema algorítmico de búsqueda
```pseudocode
ESQUEMA ALGORÍTMICO:
    Comenzar; { Establecimiento inicial del invariante si es necesario}
    MIENTRAS (EA != MarcaFin) Y NO Pro(EA) HACER
        { Tratamientos para mantener el invariante }
        Avanzar
    FIN_MIENTRAS;
    SEGÚN EA
        EA = MarcaFin : { Tratamiento elemento no encontrado }
        EA != MarcaFin : { Tratamiento EA encontrado }
    FIN_SEGÚN;
```
*(Si la marca de fin no es significativa y es erróneo acceder a ella, puede ser necesario usar `YDESPUÉS`: `MIENTRAS (EA != MarcaFin) YDESPUÉS NO Pro(EA) HACER`)*.

**Ejemplo**: Existencia de una 'A' en un texto (sec. de caracteres).
```pseudocode
Léxico
    S : secuencia de Carácter;
Algoritmo
    Comenzar(S);
    MIENTRAS (EA != MarcaFin) Y (EA(S) != 'A') HACER
        Avanzar(S)
    FIN_MIENTRAS;
    SEGÚN EA(S)
        EA(S) = MarcaFin : Escribir("No hay ninguna A");
        EA(S) != MarcaFin : Escribir("Hay al menos una A");
    FIN_SEGÚN;
Fin.
```

### Búsqueda con garantía de éxito
Si se sabe que al menos un elemento cumple la propiedad, se puede omitir la comparación con la marca de fin.
Problema: ¿Un texto es blanco?
```pseudocode
Léxico
    S : Secuencia de Carácter;
Algoritmo
    Comenzar(S);
    MIENTRAS EA(S) = ' ' HACER
        Avanzar(S)
    FIN_MIENTRAS;
    SEGÚN EA(S)
        EA(S) = MarcaFin : Escribir("Texto blanco");
        EA(S) != MarcaFin : Escribir("Texto no blanco");
    FIN_SEGÚN
FIN.
```

### Ejemplos de Búsqueda

**Comprobar si existen al menos x ocurrencias de un carácter c:**
*   Propiedad buscada: `(e = c) Y NroOcur(c, Piz) = x - 1`
*   Invariante: `noc = NroOcur(c, Piz) Y noc < x`

```pseudocode
Léxico
    S : secuencia de Carácter;
    x : Entero > 0; noc : Entero; c : Carácter;
Algoritmo
    Comenzar(S);
    Leer(x, c); noc <- 0;
    MIENTRAS (EA(S) != MarcaFin) Y ((EA(S) != c) O (noc != x - 1)) HACER
        SI EA(S) = c ENTONCES noc <- noc + 1 FIN_SI;
        Avanzar(S)
    FIN_MIENTRAS;
    SEGÚN EA(S)
        EA(S) = MarcaFin : Escribir(c, " no aparece ", x, " veces");
        EA(S) != MarcaFin : Escribir(c, " aparece al menos ", x, " veces");
    FIN_SEGÚN
FIN.
```

**Determinar si un texto contiene las letras 'A', 'E' e 'I' en este orden:**
Se requieren tres búsquedas distintas secuenciales, usando la acción parametrizada `BuscarLetra`.
```pseudocode
BuscarLetra : acción (dato c : Carácter; dato-resultado S : secuencia de Carácter)
// Las secuencias siempre las pasaremos como dato-resultado pues, aunque
// no modifiquemos su valor, si avanzamos modificamos su estado interno
Pre : { Estado(S) = consulta }
Post : { (EA(S) = c) O (EA(S) = MarcaFin) }
Algoritmo
    MIENTRAS (EA(S) != MarcaFin) Y (EA(S) != c) HACER
        Avanzar(S)
    FIN_MIENTRAS
FIN;
```
```pseudocode
Léxico
    S : secuencia de Carácter;
    BuscarLetra : acción (dato c : Carácter; dato-resultado S : secuencia de Carácter)
Algoritmo
    Comenzar(S);
    BuscarLetra ('A', S);
    SEGÚN EA(S)
        EA(S) = MarcaFin : Escribir("No");
        EA(S) != MarcaFin :
            BuscarLetra ('E', S);
            SEGÚN EA(S)
                EA(S) = MarcaFin : Escribir("No");
                EA(S) != MarcaFin :
                    BuscarLetra ('I', S);
                    SEGÚN EA(S)
                        EA(S) = MarcaFin : Escribir("No");
                        EA(S) != MarcaFin : Escribir("Sí");
                    FIN_SEGÚN
            FIN_SEGÚN
    FIN_SEGÚN
FIN.
```

**Dadas S1 y S2 determinar si son iguales:**
Búsqueda de su primera diferencia recorriendo ambas simultáneamente.
```pseudocode
Léxico
    S1, S2 : secuencia de Carácter;
Algoritmo
    Comenzar(S1); Comenzar(S2);
    MIENTRAS (EA(S1) != MarcaFin) Y (EA(S2) != MarcaFin) Y (EA(S1) = EA(S2)) HACER
        Avanzar(S1); Avanzar(S2)
    FIN_MIENTRAS;
    SEGÚN EA(S1), EA(S2)
        (EA(S1) = MarcaFin) Y (EA(S2) = MarcaFin) : Escribir("Son iguales");
        EN_OTRO_CASO : Escribir("Son diferentes");
    FIN_SEGÚN
FIN.
```

---

## 4.4 Combinación de esquemas de recorrido y búsqueda

En la práctica los esquemas de recorrido y búsqueda aparecen combinados. Para resolverlos es preciso identificar la naturaleza de cada subproblema y establecer cómo se combinan: anidados (dentro de otro tratamiento) o compuestos de forma secuencial.

**Ejemplo 1 (Anidado): Elementos de S1 en S2**
Dadas S1 y S2 ordenadas decrecientemente y sin elementos repetidos, determinar qué elementos de S1 están en S2. Recorrido de S1 con búsqueda anidada en S2.
```pseudocode
Léxico
    S1, S2 : secuencia de Entero;
Algoritmo
    Comenzar(S1); Comenzar(S2);
    MIENTRAS EA(S1) != MarcaFin HACER
        MIENTRAS (EA(S2) != MarcaFin) Y (EA(S2) > EA(S1)) HACER
            Avanzar(S2)
        FIN_MIENTRAS;
        SI (EA(S2) != MarcaFin) Y (EA(S2) = EA(S1)) ENTONCES
            Escribir(EA(S1), " está también en S2")
        SI_NO
            Escribir(EA(S1), " no está en S2")
        FIN_SI;
        Avanzar(S1)
    FIN_MIENTRAS
FIN.
```

**Ejemplo 2 (Secuencial): Elemento en S2 igual a suma de S1**
```pseudocode
Léxico
    S1, S2 : secuencia de Entero; suma : Entero;
Algoritmo
    Comenzar(S1);
    SEGÚN EA(S1)
        EA(S1) = MarcaFin : Escribir("Secuencia S1 vacía");
        EA(S1) != MarcaFin :
            suma <- EA(S1);
            ITERAR
                Avanzar(S1)
            DETENER EA(S1) = MarcaFin;
                suma <- suma + EA(S1)
            FIN_ITERAR;
            Comenzar(S2);
            MIENTRAS (EA(S2) != MarcaFin) Y (EA(S2) != suma) HACER
                Avanzar(S2)
            FIN_MIENTRAS;
            SI EA(S2) = MarcaFin ENTONCES Escribir("No")
            SI_NO Escribir("Sí")
            FIN_SI
    FIN_SEGÚN
FIN.
```

---

## 4.5 Generalización de los modelos de acceso secuencial

El acceso secuencial se distingue por dos características:
1.  **Disponibilidad del primer elemento:** Inmediata (`DP`) o necesidad de avanzar (`¬DP`).
2.  **Detección del final:** Al sobrepasar el último elemento (`FS`) o estando justo en éste (`¬FS`).

| | DP | ¬DP |
| :--- | :--- | :--- |
| **FS** | primer modelo | cuarto modelo |
| **¬FS**| tercer modelo | segundo modelo |

### Primer modelo (DP y FS)
Disponemos del EA tras `Comenzar(DP)`. Detectamos el final al llegar a `MarcaFin` (FS).
Si no hay MarcaFin sino función booleana `FDS`, el orden de iteración `Comprobar -> Tratar -> Avanzar` se mantiene, debiendo usar operadores como `YDESPUÉS` y `ODESPUÉS`.
*   ESQUEMA 1 (H1 y H2):
```pseudocode
Comenzar;
{ Inicialización del tratamiento }
MIENTRAS NO FDS HACER
    { Tratamiento de EA }
    Avanzar
FIN_MIENTRAS;
{ Terminación del tratamiento }
```
*   ESQUEMA 2 (¬H1 y H2):
```pseudocode
Comenzar;
SEGÚN FDS
    FDS :
        { Tratamiento de sec. vacía }
    NO FDS :
        { Inicialización del tratamiento }
        REPETIR
            { Tratamiento de EA }
            Avanzar
        HASTA FDS:
        { Terminación del tratamiento }
FIN_SEGÚN;
```
*   ESQUEMA 3 (¬H1 y ¬H2):
```pseudocode
Comenzar;
SEGÚN FDS
    FDS :
        {Tratamiento sec. vacía }
    NO FDS :
        { Tratamiento 1er elemto. }
        ITERAR
            Avanzar
            DETENER FDS;
            { Tratamiento de EA }
        FIN_ITERAR;
        { Terminación del tratto. }
FIN_SEGÚN;
```

*   ESQUEMA DE BÚSQUEDA:
```pseudocode
Comenzar; // Inicialización del invariate*
MIENTRAS NO FDS
        YDESPUÉS NO Pro(EA) HACER
    // TTos. para mantener el invariante*
    Avanzar
FIN_MIENTRAS;
SEGÚN FDS
    FDS : { Tratto. elemento no encontrado }
    NO FDS : { Tratamiento EA encontrado }
FIN_SEGÚN;
```

En el caso de la búsqueda es necesario usar **YDESPUÉS** para no acceder a EA cuando éste ya no está disponible.

\* si los hay

### Segundo modelo (¬DP y ¬FS)
La mayoría de los accesos seciales sigue los modelos primero o segundo. El tercer modelo nos resultará útil para hacer búsquedas en tablas, aunque no lo estudiaremos formalmente.

El primer elemento no está disponible tras iniciar (es preciso `Avanzar`). El final se detecta estando sobre el último elemento significativo.

El conjunto de estados ahora será `{ninguno, creación, iniciada, consulta}`

### Operaciones Primitivas (Segundo Modelo):
**Acceso Secuencial**
*   `Iniciar(S)`: Inicia la consulta. Su primer elemento no está disponible.
*   `Avanzar(S)`: Avanza al siguiente elemento de S.
*   `EA(S)`: Retorna el elemento actual de S.
*   `EsVacía(S)`: Función booleana (Verdadero si S está vacía).
*   `EsÚltimo(S)`: Función booleana (Verdadero si ya no es posible Avanzar).

**Creación Secuencial**
*   `Crear(S)`: Crea S como una secuencia vacía sobre la que podemos añadir elementos por la derecha
*   `Registrar(S, e)`: Graba el elemento e como último elemento de una secuencia S

| | ninguno | creación | iniciada | consulta |
| :--- | :---: | :---: | :---: | :---: |
| **Iniciar** | X | iniciada | iniciada | iniciada |
| **Avanzar** | X | X | consulta | consulta |
| **EA** | X | X | X | consulta |
| **EsVacía** | ninguno | creación | iniciada | consulta |
| **EsÚltimo** | X | X | iniciada | consulta |
| **Crear** | creación | creación | creación | creación |
| **Registrar** | X | creación | X | X |

**Esquema 1 (H1 y H2):**
```pseudocode
Iniciar;
{ Inicialización del tratamiento }
MIENTRAS NO EsÚltimo HACER
    Avanzar
    { Tratamiento de EA }
FIN_MIENTRAS;
{ Terminación del tratamiento }
```

**Esquema 2 (¬H1 y H2):**
```pseudocode
Iniciar;
SEGÚN EsVacía
    EsVacía : 
        { Tratamiento sec. vacía }
    NO EsVacía :
        { Inic. del tratamiento }
        REPETIR
            Avanzar
            { Tratamiento de EA }
        HASTA EsÚltimo;
        { Terminación del tratto. }
FIN_SEGÚN;
```

**Esquema 3 (¬H1 y ¬H2):**
```pseudocode
Iniciar;
SEGÚN EsVacía
    EsVacía : 
        { Tratamiento sec. vacía }
    NO EsVacía :
        Avanzar
        { Tratamiento 1er elemento }
        MIENTRAS NO EsÚltumo HACER
            Avanzar;
            { Tratamiento de EA }
        FIN_MIENTRAS;
        { Terminación del tratto. }
FIN_SEGÚN;
```

**Esquema de Búsqueda:**
```pseudocode
Iniciar;
SEGÚN EsVacía
    EsVacía : { Tratamiento: no encontrado }
    NO EsVacía : // Inicialización invariante*
        REPETIR
            Avanzar // y TTos. mantener invar.*
        HASTA EsÚltimo O Pro(EA);
        SEGÚN EA
            Pro(EA) : 
                { Tratamiento EA encontrado }
            NO Pro(EA) : 
                { Tratamiento: no encontrado }
        FIN_SEGÚN
FIN_SEGÚN;
```
\* si los hay

**Diferencia de Ciclos de Iteración:**
En general, los dos modelos de acceso secuencial se van a diferenciar por  el orden en el que hacemos los tres tratamientos elementales del ciclo de la iteración: **comprobación** del fin, **tratamiento** del `EA` y **avance**:
```text
Primer Modelo:      Comprobar -> Tratar -> Avanzar
Segundo Modelo:     Comprobar -> Avanzar -> Tratar
```
Esto se debe a las diferencias entre ambos modelos en el inicio  (disponibilidad o no del primer elemento tras el inicio) y en la detección del  final (al sobrepasar el último elemento significativo o al estar sobre él)

**Ejemplo: Media aritmética (Segundo modelo):**
*   Solución 1 (H1 y H2):
```pseudocode
Iniciar(S);
suma <- 0.0; n <- 0;
MIENTRAS NO EsÚltimo(S) HACER
    Avanzar(S);
    suma <- suma + EA(S); n <- n + 1
FIN_MIENTRAS;
SEGÚN n
    n = 0 : Escribir("Secuencia vacía");
    n > 0 : media <- suma / n;
            Escribir(media);
FIN_SEGÚN
```
*   Solución 2 (¬H1 y H2):
```pseudocode
Iniciar(S);
SEGÚN EsVacía(S)
    EsVacía(S) :
        Escribir("Secuencia vacía");
    NO EsVacía(S) :
        suma <- 0.0; n <- 0;
        REPETIR
            Avanzar(S);
            suma <- suma + EA(S);
            n <- n + 1
        HASTA EsÚltimo(S);
        media <- suma / n;
        Escribir(media)
FIN_SEGÚN;
```

*   Solución 3 (¬H1 y ¬H2):
```pseudocode
Iniciar(S);
SEGÚN EsVacía(S)
    EsVacía(S) :
        Escribir("Secuencia vacía");
    NO EsVacía(S) :
        Avanzar(S);
        suma <- EA(S); n <- 1;
        MIENTRAS NO EsÚltimo(S) HACER
            Avanzar(S);
            suma <- suma + EA(S);
            n <- n + 1
        FIN_MIENTRAS;
        media <- suma / n;
        Escribir(media)
FIN_SEGÚN;
```

**Ejemplo de Búsqueda: ¿Un texto es blanco?**
```pseudocode
Iniciar(S);
SEGÚN EsVacía(S)
    EsVacía(S) : Escribir("Texto vacío");
    NO EsVacía(S) :
        REPETIR
            Avanzar(S);
        HASTA EsÚltimo(S) O EA(S) != ' ';
        SI EA(S) != ' ' ENTONCES
            Escribir("Texto no blanco")
        SI_NO
            Escribir("Texto blanco")
        FIN_SI
FIN_SEGÚN;
```