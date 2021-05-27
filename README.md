# "El fantasma" - Una micro aventura interactiva.

El fantasma es una aventura interactiva, con un motor esta escrito utilizando javascript vainilla, [Bulma](https://bulma.io/) CSS y [Pako](https://github.com/nodeca/pako).

Creada para la game jam [Rayuela de Arena 2021](https://itch.io/jam/rayuela-de-arena-2021).

Los archivos fuente están escritos en un lenguaje de marcado propio llamado Borges (de ahí la extensión *.brgs*). La extensión para resalto de sintaxis en vscode esta incluida también aquí en el directorio `borges-markup`.

El parser (borges.py) recibe el primer archivo de entrada y los procesa para generar un archivo json (result.json) y una versión comprimida del mismo en el directorio `juego/assets` (data.dat), que es después utilizada por el motor.

Puede ser jugada en itch.io [aquí](https://lacalaveraverde.itch.io/el-fantasma)

![imagen](/juego/assets/viñedo.png)

Todo el arte y la hisotria esta bajo una [Licencia Creative Commons de Atribución Internacional 4.0](http://creativecommons.org/licenses/by/4.0/)