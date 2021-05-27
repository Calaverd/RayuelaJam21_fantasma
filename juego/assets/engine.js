
let historia = {}; 

// Revisa un verso, si en el verson encuentra algo de la forma $var$
// buscara una variable de ese nombre, y la remplazara
function parseVars(text){
    let matches = text.match(/\$[a-zA-Z]+([A-z0-9_.-]*)+\$/g);
    if(matches !== null){
        matches = [...new Set(matches)]; // retirar duplicados
        matches.forEach(
          match => {
            let nm = match.slice(1, -1);
            text = text.replaceAll(match,String(historia['_VAR_'][nm]));
        });
    }
    return text    
}

// esta funcion literalmente remplaza en una cadena la variable $vars$
// por lo que esta referencia 
function parseVarsPure(text){
    let matches = text.match(/\$[a-zA-Z]+([A-z0-9_.-]*)+\$/g);
    if(matches !== null){
        matches = [...new Set(matches)]; // retirar duplicados
        matches.forEach(
          match => {
            let nm = match.slice(1, -1);
            text = text.replaceAll(match,`historia['_VAR_']['${nm}']`);
        });
    }
    //console.log(text);
    return text    
}

function evalua(expresion){
    return eval(parseVarsPure(expresion));
}

function setVarValue(var_name,value){
    historia['_VAR_'][var_name] = value
}

let current_page = '';
let destiny_page = '';
let current_text = 0;
let current_animation_end = true;
let added_buttons = false;
let button_css_class = 
 ('button is-black has-background-grey-dark is-medium is-fullwidth my-3 b-intro is-size-4-desktop is-multiline').split(' ');

let focus_button = -1;

function checkCurrentAnimationEnded(event){
    if(event.type === "animationend"){
        current_animation_end = true;
    }      
};

function createOption(option_section, option_text, option_id, number, str_evaluar){
    let element = document.createElement("button");

    element.innerHTML = parseVars(option_text);
    element.id = option_id;

    button_css_class.forEach(
        css_class => { element.classList.add(css_class) } );
    element.addEventListener("animationend", checkCurrentAnimationEnded, false);
    //make the button active also if focus and enter pressed
    element.addEventListener('keydown',(e) => {
        if (e.key == 'Enter') {
            fadeOutButtons(element);
            fadeOutText();
            };
       }, false);

    element.addEventListener('mouseover',function(){
        if( current_animation_end){
            element.focus();
        }}, false);

    element.addEventListener('focusout',function(){
            element.classList.remove('has-text-weight-bold');
           }, false);

    const num = number.valueOf();
    element.addEventListener('focus',function(){
        //console.log('Focus on button ', num);
        element.classList.add('has-text-weight-bold');
        focus_button = num;
       }, false);
    
    //console.log('A ejecutar en mouseup', str_evaluar);
    element.addEventListener('mouseup',function(){
        //console.log('Ejcutando', str_evaluar);
        if(current_animation_end){
          evalua(str_evaluar);
          }
        }, false);
       
    if(number == 0){
        element.setAttribute("tabindex",String(number));
    };
    
    option_section.appendChild(element);
}

function addNextElement(){
    //console.log('Add next element');
    //console.log(current_page,historia[current_page].text.length, current_text);
    if(current_animation_end){
        current_animation_end = false;
        // if not more text, then add the options...
        if(historia[current_page].text.length > current_text){
            var element = document.createElement("p");
            element.innerHTML = parseVars(historia[current_page].text[current_text]);
            element.classList.add("is-size-5");
            element.classList.add("is-size-4-desktop");
            element.classList.add("my-3");
            element.classList.add("fade-in");
            // element.addEventListener("animationend", checkCurrentAnimationEnded, false);
            current_animation_end = true;

            document.getElementById('texto').appendChild(element);

            current_text++;

        } else if( !added_buttons ){
            added_buttons = true;
            //console.log('typeof input is... ', historia[current_page].input );
            if( historia[current_page].input !== undefined){
                let str_evaluar = '';
                if(historia[current_page].input.asignar !== undefined){
                    str_evaluar = historia[current_page].input.asignar;
                }
                if(historia[current_page].input.condicion !== undefined){
                    if(eval(parseVars(historia[current_page].input.condicion))){
                        addForm(str_evaluar,var_name,historia[current_page].input.var);
                    }
                }else{
                    addForm(str_evaluar,historia[current_page].input.var);
                }
            } else if(historia[current_page].options !== undefined ){
                let option_section = document.getElementById('opciones')
                let index_b = 0;
                historia[current_page].options.forEach(
                    option => {
                        let str_evaluar = '';
                        if(option.asignar !== undefined){
                            str_evaluar = option.asignar;
                        }
                        // esta es mi cosa favorita de los lenguajes interpretados
                        // solo revizan la segunda condicion en un "or" si la primera es falsa
                        if(option.condicion === undefined || eval(parseVars(option.condicion)) ){
                            if(option[0] !== undefined && option[1] !== undefined){
                                createOption(option_section, option[0], option[1], index_b, str_evaluar);
                                index_b++;
                            }else if(option.text !== undefined && option.destino !== undefined){
                                createOption(option_section, option.text, 
                                    option.destino, index_b, str_evaluar);
                                index_b++;
                            }else if(option.destino !== undefined){
                                // no tiene definido texto
                                destiny_page = option.destino;
                                clearArea();
                            }
                        }
                });
            }else if((typeof historia[current_page].options) === "string"){
                destiny_page = historia[current_page].options;
                clearArea();
            }
        }
    }
}

function fadeOutButtons(target){
    destiny_page = target.id;
    target.classList.add('b-c-exit');
    let all_b = document.getElementsByTagName('BUTTON');
    for (var i = 0; i < all_b.length; i++) {
        if(all_b[i] !== target){
           all_b[i].classList.add('b-exit');
        }
    };
};

function fadeOutText(){
    // add fade out animation a todo el texto...
    let all_t = Array.from(document.getElementById('texto').childNodes);
    let added_listener = false;
    for (var i = 0; i < all_t.length; i++) {
        if(all_t[i].classList){
            all_t[i].classList.remove("fade-in");
            all_t[i].classList.add('fade-out');
            if(! added_listener){
                // en el primer elemento agregamos un listener para limpiarlo todo
                added_listener = true
                all_t[i].addEventListener("animationend", clearArea, false);
            }
        } else{
            //console.log(all_t[i]);
        }
    };
}

function checkInput(variable_a_asignar){
    let sanitized = document.getElementById("input").value.replaceAll(/<[\/\w\.\s-]*>/g,'');
    variable_a_asignar = variable_a_asignar.slice(1, -1);
    const send = window[historia[current_page].input.fun](variable_a_asignar,sanitized);
    destiny_page = historia[current_page].input.destinos[send];
    let input = document.getElementById('input');
    let inputb =  document.getElementById('input-button');
    input.classList.remove("fade-in");
    input.classList.add('fade-out');
    inputb.classList.remove("fade-in");
    inputb.classList.add('fade-out');
    fadeOutText();
};

function addForm(str_evaluar,variable_a_asignar){
    let input_section = document.getElementById('opciones')
    let form = document.createElement("div");
    form.classList.add('field');
    form.classList.add('has-addons');
    let divi = document.createElement("div");
    divi.classList.add('control');
    divi.classList.add('is-expanded');
    let input = document.createElement("input");
    input.classList.add('input');
    input.classList.add('is-black');
    input.classList.add('is-medium');
    input.classList.add('has-background-grey-dark');
    input.classList.add('has-text-white');
    input.classList.add('fade-in');
    input.classList.add('is-size-4-desktop');
    input.setAttribute("type", "text");
    input.setAttribute("id", "input");
    let divb = document.createElement("div");
    divb.classList.add('control');
    let button = document.createElement("a");
    button.classList.add('button');
    button.classList.add('is-black');
    button.classList.add('has-background-grey-dark')
    button.classList.add('is-medium');
    button.classList.add('fade-in');
    button.classList.add('is-size-4-desktop');
    button.setAttribute("id", "input-button");
    button.setAttribute("tabindex","0");
    button.innerHTML = 'Aceptar';

    current_animation_end = false;

    divb.appendChild(button);
    divi.appendChild(input);
    form.appendChild(divi);
    form.appendChild(divb);
    input_section.appendChild(form);

    
    input.addEventListener("animationend",function(){
        current_animation_end = true;
        let element = document.getElementById('input');
        if( element != null){
            document.getElementById('input').focus();
        }
       }, false);
    
    input.addEventListener('mouseover',function(){input.focus();}, false);

    let evaluada = false
    let evalua_exp = function() {
        if(! evaluada){
            evalua(str_evaluar);
            evaluada = true;
        }
    };
    
    input.addEventListener('keydown',(e) => {
        if (e.key == 'Enter') {
            checkInput(variable_a_asignar);
            evalua_exp()
            };
       }, false);
    
    button.addEventListener('keydown',(e) => {
        if (e.key == 'Enter') {
            checkInput(variable_a_asignar);
            evalua_exp()
            };
       }, false);
    
    button.addEventListener('mouseover',function(){button.focus();}, false);
    button.addEventListener('mouseup',function(){checkInput(variable_a_asignar);}, false);

    button.addEventListener('focusout',function(){
        button.classList.remove('has-text-weight-bold');
       }, false);
    
    button.addEventListener('focus',function(){
        button.classList.add('has-text-weight-bold');
       }, false);
    
       element.addEventListener('mouseup',function(){
        // console.log('Ejcutando', str_evaluar);
        evalua(str_evaluar);
        }, false);
};

function clearArea(){
    document.getElementById("texto").textContent = '';
    document.getElementById("opciones").textContent = '';
    //document.getElementById("entrada").textContent = '';
    current_page = destiny_page;
    destiny_page = '';
    current_text = 0;
    current_animation_end = true;
    added_buttons = false;
    focus_button = -1;
    //set the focus again on the body
    //document.body.focus();
    addNextElement();
};

document.addEventListener('keyup',(e) => {
    let all_b = document.getElementsByTagName('BUTTON');
    if(all_b.length > 0){
        if(e.key == 'ArrowUp'){
            //console.log('UP');
            focus_button-=1
            if( focus_button < 0){
                focus_button = 0;
            }
            all_b[focus_button].focus()
        }
        if(e.key == 'ArrowDown'){
            //console.log('Donw');
            focus_button+=1
            if( focus_button >=  all_b.length ){
                focus_button = all_b.length-1;
            }
            all_b[focus_button].focus()
        }
    }
});

document.addEventListener('keydown',(e) => {
    if (e.key == ' ' || e.key == 'Enter') {
       addNextElement();
    };
});

document.onclick = function(event) {
    if (event===undefined) event= window.event;
    addNextElement();
};


// botones solo son disparados cuando el mouse se levanta
document.onmouseup = function(event) {
    if (event===undefined) event= window.event;

    let target= 'target' in event? event.target : event.srcElement;
    if(target.tagName == 'BUTTON'){
        fadeOutButtons(target);
        fadeOutText();
    };

};

function loadJsonData(json_url){
    const request_data = new Request(json_url);
    const promesa = fetch(request_data).then(
        function(response) {
            return response.arrayBuffer();
        }).then(function(buffer) {
            let my_data = new Uint8Array(buffer);
            historia = JSON.parse(pako.inflate(my_data, { to: 'string' }));
            current_page = historia['_START_'];
            addNextElement();
        });
};