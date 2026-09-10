El objetivo de este primer proyecto busca responder siguiente pregunta:

¿Cuál es el mejor fin de semana largo del año para escaparse en Uruguay, y
adónde?

El proyecto se dividira en distintos hitos. Cada uno de estos representara distintas etapas las cuales se 
documentaran los procesos del trabajo.
Los siguientes incluiran:
-Desiciones
-Inconvenientes
-Procedimientos
-Aprendizajes

El fundamento y lo primero en lo que se basa nuestro trabajo es en la eleccion de la API. Luego de una busqueda exhaustiva,
necesiabamos una API que cumpla nustras necesidades. En ese momento dimos con FOURSQUARE API. 

FOURSQUARE permitia solicitar las ubicaciones de interes cerca de un lugar. Detectava y devolvia ubicaciones de restaurantes, boliches, zonas de entretenimiento,
atracciones, etc. Esta posibilidad seria crucial y de gran ayuda para responder a la pregunta.
Finalmente, terminamos por descartar la API debido a que, para usarla, debiamos ingresar un metodo de pago como parte del registro.

HITO 1:
Comenzamos creando un repositorio en GIT para poder trabajar de forma sincronica. Utilizamos pycharm como motor de nuestro trabajo.
Creamos la carpeta indice-escapada la cual seria el paradero de nuestros archivos.
Creamos la carpeta solicitada en los requisitos llamada 'config', dentro de esta, esta el archivo 'ubicaciones.json'
    Elegimos el lugar de partida:

                            - MONTEVIDEO
    Elegimos los destinos: 

                            - COLONIA DEL SACRAMENTO
                            - CARMELO
                            - PIRIAPOLIS
                            - PUNTA DEL ESTE
                            - JOSE IGNACIO
                            - LA PALOMA
                            - CABO POLONIO
                            - PUNTA DEL DIABLO
                            - AGUAS DULCES
                            - MINAS
                            - VILLA SERRANA 
                            - TERMAS DEL DAYMAN
                            - SALTO
                            - MERCEDES
                            - TACUAREMBO
    
Agregamos al achivo ubicaciones.json el lugar de partida y los destinos, cada uno con una id respectiva y su forma de llamarlos en la API.
Creamos la carpeta SRC, dentro tiene dos archivos: 
-geocoding.py
Este archivo se compone de 4 funciones principales.
cargar_ubicaciones: extrae un punto de origen y una lista de destinos, devolviendo una lista unificada.
cargar_cache: verifica si existe el archivo de cache, sino devuelve un diccionario vacio. Si existe, lee la informacion y devuelve el diccionario con la informacion previa.
guardar_cache: toma los resultados obtenidos y los guarda para el futuro.
buscar_coordenadas: se comunica directamente con la API para obtener las coordenadas
geocodificar_todo: esta funcion es el motor de todo, ordena y orquesta todas las funciones anteriores. Maneja errores y va guardando datos

-weather.py



