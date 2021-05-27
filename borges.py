#!/usr/bin/python3
#_*_ coding: utf-8 _*_

help_msg = """
Borges Parser 
Escrito por Calaverd (Osvaldo Guadalupe Barajas Fierros) - 2021

Uso:

 python ./borges.py nombre_archivo.brgs [Opciones]

Opciones: 

-i, --input  : Un archivo .brgs para trabajar, por defecto, el primer argumento.
-p, --pagina : Nombre de una pagina que fijar como punto de entrada. 
-h, --help   : Este mensaje de ayuda.

"""


from sys import argv
from os import path, listdir
import getopt
import re
import json
import zlib

def cleanDic(d):
  for key, value in list(d.items()):
    if not value and not isinstance(value, bool):
      del d[key]
    elif isinstance(value, dict):
      cleanDic(value)
  return d

regex_comblock   = re.compile(r'\/\*.*?(?:\*\/)', re.DOTALL|re.MULTILINE)
regex_comline  = re.compile(r'(?:\/\/).*?(?:$)', re.DOTALL|re.MULTILINE)
regex_page   = re.compile(r'(?:##).*?(?=#|\Z)', re.DOTALL|re.MULTILINE)
regex_page_title     = re.compile(r'(?<=##).*?(?:\n|\r)',re.DOTALL)
regex_option_pattern = re.compile(r':\).*?(?<!\\)(?:!)',re.DOTALL|re.MULTILINE)
regex_input_pattern  = re.compile(r'<:.*?(?:!)',re.DOTALL|re.MULTILINE)
regex_condition_opt  = re.compile(r'(?<=:\)).*?(?<!\\)(?=\?)',re.DOTALL|re.MULTILINE)
regex_condition_inp  = re.compile(r'(?<=<:).*?(?<!\\)(?=\?)',re.DOTALL|re.MULTILINE)
regex_string_pattern = re.compile(r'(?<=\s").+?(?<!\\)(?=")',re.DOTALL|re.MULTILINE)
regex_io_str_pattern = re.compile(r'(?<=").+?(?<!\\)(?=")',re.DOTALL|re.MULTILINE)
regex_destin_pattern = re.compile(r'(?<=\->).*?(?=!|\(|\$|\{)',re.DOTALL|re.MULTILINE)
regex_asigment_pttrn = re.compile(r'\{\{.*?(?:\}\})',re.DOTALL|re.MULTILINE)
regex_function = re.compile(r'(?<=\().*?(?=\))',re.DOTALL|re.MULTILINE)
regex_var_name = re.compile(r'\$[a-zA-Z]+[A-z0-9_.-]*\$')
regex_require  = re.compile(r'(?<=@require).*?(?=$)', re.DOTALL|re.MULTILINE)
# esta cosa fea de aquí significa "cualquier cosa de la forma $var$ = bool num string"
regex_var_declaration = re.compile(r'\$.*\$\s*=\s*(false|true|[0-9]+|\"(.|\n)*?(?<!\\)\")',re.MULTILINE)


def getIgnorePoints(regex, str):
  ignore_points = []
  for m in regex.finditer(str):
    ignore_points.append( (m.start(), m.end()) )
  return ignore_points

def getLine(line_pos_list,postition):
  for j in range(len(line_pos_list)):
    if line_pos_list[j] > postition:
      return j+1
  return len(line_pos_list)+1

def parseNode(use_regex, points_to_ignore, search_str):
  list_nodes = []
  for m in use_regex.finditer(search_str):
    
    comienzo = m.start()
    ignore = False
    for point in points_to_ignore:
      if comienzo > point[0] and comienzo < point[1]:
        ignore = True
        break
    if not ignore:
      #print(m.group(0))
      node = {}
      node['text']   = m.group(0)
      node['start']  = m.start()
      node['end']    = m.end()
      list_nodes.append(node)
  return list_nodes

historia = {}
historia['_VAR_'] = {}

class Var:
  def __init__(self):
    # revisar los diferentes usos de la variable
    self.definition = None
    self.value = ""
    self.declared_on = []
    self.asignaciones = []
    self.condicionales = []
    self.cadenas = []
  def __str__(self):
    string = "Definición "+str(self.definition)+' \n'
    string += "Value "+str(self.value)+' ('+str(type(self.value))+')'
    if self.cadenas:
      string += "\n  Cadenas:\n"
      for a in self.cadenas:
        string += '    '+str(a[0])+' en linea '+str(a[1])+'\n'
    if self.asignaciones:
      string += "\n  Asignaciones:\n"
      for a in self.asignaciones:
        string += '    '+str(a[0])+' en linea '+str(a[1])+'\n'
    if self.condicionales:
      string += "\n  Condiciones:\n"
      for a in self.condicionales:
        string += '    '+str(a[0])+' en linea '+str(a[1])+'\n'
    return string


conteo_de_variables = {}
archivos_a_procesar = []
archivos_procesados = []

def agregaVariables(lista_variables, pagina, linea, tipo_lugar):
  for var in lista_variables:
    var = var[1:-1]
    if not var in conteo_de_variables:
      conteo_de_variables[var] = Var()
    if tipo_lugar == 'asignacion':
      conteo_de_variables[var].asignaciones.append( (pagina,linea) )
    if tipo_lugar == 'condicional':
      conteo_de_variables[var].condicionales.append( (pagina,linea) )
    if tipo_lugar == 'cadena':
      conteo_de_variables[var].cadenas.append( (pagina,linea) )

def agregaVariables(lista_variables, pagina, linea, tipo_lugar):
  for var in lista_variables:
    var = var[1:-1]
    if not var in conteo_de_variables:
      conteo_de_variables[var] = Var()

list_of_pages = {}
list_of_links = {}
list_of_functions = {}
list_of_vars = []

def procesarArchivos():
  #global list_of_links

  start_page_asignada = False
  for archivo in archivos_a_procesar:
    file = open(archivo,"r")
    file_str = file.read()
    file.close()

    len_file = len(file_str)
    end='.*\n'
    file_endline_positions=[]
    for m in re.finditer(end, file_str):
        file_endline_positions.append(m.end())

    ignorepoints = getIgnorePoints(regex_comblock, file_str)
    ignorepoints += getIgnorePoints(regex_comline, file_str)
    ignorepoints += getIgnorePoints(regex_string_pattern, file_str)

    page_list = parseNode(regex_page, ignorepoints, file_str)

    list_of_declared_vars = parseNode(regex_var_declaration, ignorepoints, file_str)
    for var in list_of_declared_vars:
      vartext = var['text']
      varname = regex_var_name.findall(vartext)[0][1:-1]
      vartext = regex_var_name.sub('',vartext).replace('=','')
      vartext = vartext.replace('false',"False")
      vartext = vartext.replace('true',"True")
      varvalue = eval(vartext)
      line_num =  getLine(file_endline_positions,var['start'])
      declaracion = " Declaración en archivo "+archivo+", "
      declaracion += 'en la linea '+str(line_num)+' '
      declaracion += "con valor \""+str(varvalue)+"\" de tipo "+str(type(varvalue))
      if not varname in conteo_de_variables:
        conteo_de_variables[varname] = Var()
      else:
        print(varname, 'esta siendo redefinida en ', archivo)
      conteo_de_variables[varname].definition = True
      conteo_de_variables[varname].declared_on.append(declaracion) 
      conteo_de_variables[varname].value = varvalue

    list_of_rfiles = []
    required_matchs = parseNode(regex_require, ignorepoints, file_str)
    for match in required_matchs:
      list_of_rfiles += list(map(str.strip,match['text'].split(',')))

    for rfile in list_of_rfiles:
      is_file = False
      if path.isfile(rfile+'.brg'):
        rfile = rfile+'.brg'
        is_file = True
      elif path.isfile(rfile+'.brgs'):
        rfile = rfile+'.brgs'
        is_file = True
      else:
        print("Advertencia: ",rfile," no existe o no es un archivo.") 
      
      if is_file and not rfile in archivos_procesados and not rfile in archivos_a_procesar:
        archivos_a_procesar.append(rfile)


    for page in page_list:
      page_title = regex_page_title.findall(page['text'])[0].strip()
      # la primera pagina del primer archivo procesado siempre es la
      # pagina de entrada...
      if not start_page_asignada:
        start_page_asignada = True
        historia['_START_'] = page_title

      opciones = parseNode(regex_option_pattern,[],page['text'])
      input_p = parseNode(regex_input_pattern,[],page['text'])

      ignore_points = getIgnorePoints(regex_option_pattern,page['text'])
      ignore_points += getIgnorePoints(regex_input_pattern,page['text'])

      texto = parseNode(regex_string_pattern,ignore_points,page['text'])
      
      #print(getLine(file_endline_positions,page['start'])," Title:",page_title)
      historia[page_title] = {}
      historia[page_title]['text'] = []
      historia[page_title]['options'] = []

      for i in range(len(texto)):
        texto[i]['text'] = texto[i]['text'].strip().replace('\\"','"').replace('\n','<br>')
        historia[page_title]['text'].append(texto[i]['text'])
        #print(getLine(file_endline_positions,page['start']+texto[i]['start'] ),"  :",texto[i]['text'])
        line = getLine(file_endline_positions,page['start']+texto[i]['start'] )
        agregaVariables(regex_var_name.findall(texto[i]['text']),
                (archivo+' : '+page_title), line, "cadena")
      
      if not page_title in list_of_pages:
        list_of_pages[page_title] = []
      list_of_pages[page_title].append(
        archivo+' : '+page_title+' en linea '+
          str(getLine(file_endline_positions,page['start'])))
      
      

      for opcion in opciones:
        #print(opcion.replace('\n',' '))
        opcion_text = opcion['text']
        opcion_page = page_title
        opcion_line = getLine(file_endline_positions,page['start']+opcion['start'])

        destinos_match = regex_destin_pattern.findall(opcion_text)
        condition_match = regex_condition_opt.findall(opcion_text)
        asignacion_match = regex_asigment_pttrn.findall(opcion_text)
        
        # retirar la asignación y condición para que no interfieran
        # con el resto de lo que vamos a parsear
        ignore_points = getIgnorePoints(regex_asigment_pttrn,opcion_text)
        ignore_points += getIgnorePoints(regex_condition_opt,opcion_text)

        text_match = parseNode(regex_io_str_pattern,ignore_points,opcion_text)
        
        opcion_dic = {}

        if destinos_match:
          destino = destinos_match[0].split(',')[0].strip()
          if not destino in list_of_links:
            list_of_links[destino] = []
          list_of_links[destino].append(archivo+' : '+page_title+' en linea '+str(opcion_line))
          opcion_dic['destino'] = destino
          if not text_match:
            if len(opciones) > 1:
              print(' Advertencia: ')
              print(' En pagina ',page_title,
                ' linea ', opcion_line )
              print(opcion_text)
              print('Opcion directa conviviendo con otras')
          if text_match:
            opcion_dic['text'] = text_match[0]['text'].strip()
            opcion_dic['text'] = opcion_dic['text'].strip().replace('\\"','"').replace('\n','<br>').replace('\?','?').replace('\!','!')
            agregaVariables(regex_var_name.findall(opcion_dic['text']),
                (archivo+' : '+page_title), opcion_line, "cadena")
          if asignacion_match:
            opcion_dic['asignar'] = asignacion_match[0].replace('\n',';')[2:-2].replace(':','=')
            agregaVariables(regex_var_name.findall(opcion_dic['asignar']),
                (archivo+' : '+page_title), opcion_line, "asignacion")
          if condition_match:
            opcion_dic['condicion'] = condition_match[0].strip().replace('~','!')
            agregaVariables(regex_var_name.findall(opcion_dic['condicion']),
                (archivo+' : '+page_title), opcion_line, "condicional")

          historia[page_title]['options'].append(opcion_dic)
      
      if input_p:
        if opciones:
          print(' Advertencia: ')
          print(' En pagina ',page_title,
                ' linea ', getLine(file_endline_positions,page['start']+input_p[0]['start'] ) )
          print(input_p[0]['text'])
          print('No puedes tener opciones y entrada en la misma pagina!!!')
        else:
          entrada = input_p[0]['text']
          entrada_linea = getLine(file_endline_positions,page['start']+input_p[0]['start'] )
          condition_match = regex_condition_opt.findall(entrada)
          asignacion_match = regex_asigment_pttrn.findall(entrada)

          # retirar la asignación y condición para que no interfieran
          # con el resto de lo que vamos a parsear
          entrada = regex_asigment_pttrn.sub('', entrada)
          entrada = regex_condition_opt.sub('', entrada)

          variable_match = regex_var_name.findall(entrada)
          function_match = regex_function.findall(entrada)
          destinos_match = regex_destin_pattern.findall(entrada)

          destinos = []
          # estos 3 campos son obligatorios
          input_dic = {}
          if destinos_match and function_match and variable_match:
            lista_destinos = list(map(str.strip,destinos_match[0].split(',')))
            for dest in lista_destinos:
              if not dest in list_of_links:
                list_of_links[dest] = []
              list_of_links[dest].append(archivo+' : '+page_title+' en linea '+str(entrada_linea))
            input_dic['destinos'] = lista_destinos
            input_dic['fun'] = function_match[0].strip()
            input_dic['var'] = variable_match[0].strip()

            if not input_dic['fun'] in list_of_functions:
              list_of_functions[input_dic['fun']] = []
            list_of_functions[input_dic['fun']].append(archivo+' : '+page_title+' en linea '+str(entrada_linea))

            agregaVariables([input_dic['var']],
                (archivo+' : '+page_title), entrada_linea, "asignacion")
            if asignacion_match:
              input_dic['asignar'] = asignacion_match[0].replace('\n','')[2:-2].replace(':','=')
              agregaVariables(regex_var_name.findall(input_dic['asignar']),
                (archivo+' : '+page_title), entrada_linea, "asignacion")
            if condition_match:
              input_dic['condicion'] = condition_match[0].strip().replace('~','!')
              agregaVariables(regex_var_name.findall(input_dic['condicion']),
                (archivo+' : '+page_title), entrada_linea, "condicional")

            historia[page_title]['input'] = input_dic
    
    archivos_procesados.append(archivo)


def cadena_a_bites(cadena):
    cadena = cadena.encode('utf-8')
    return bytes(cadena)

def escribe_archivo_comprimido(directorio, datos_a_comprimir):
    archivo = open(directorio, 'wb')
    archivo.write(zlib.compress(cadena_a_bites(datos_a_comprimir)))
    archivo.close()

def run():
  global historia
  try:
    opts, args = getopt.gnu_getopt(argv[1:],"hdi:o:p:",['input','help','output','pagina'])
  except getopt.GetoptError:
    print('borges.py archivo [opciones]')
    sys.exit(2)

  # por defecto el primero de los sobrantes es el nombre del archivo a procesar
  input_file = None
  start_page = None

  for opt, arg in opts:
    if opt in ('-i', '--input'):
        input_file = arg
    if opt in ('-p', '--pagina'):
        if arg != '':
          start_page = arg
    if opt in ('-h','--help'):
      print(help_msg)
        
  if not input_file:
    if len(args) > 0:
      input_file = args[0]
    else:
      print('Sin archivo de entrada!')
      sys.exit(2)

  if path.isfile(input_file):
    archivos_a_procesar.append(input_file)

    procesarArchivos()

    print("Archivos leídos: ")
    for archivo in archivos_procesados:
      print(' ', archivo)

    if list_of_pages != list_of_links: # tenemos paginas sin referencia o referencias sin paginas...
      for link in list_of_links:
        if not link in list_of_pages:
          print('\nEl link a '+link+' referencia una pagina que no exite')
          print('Definido en: ')
          for defi in list_of_links[link]:
            print('  ',defi)
      for page in list_of_pages:
        if not page in list_of_links and page != historia['_START_']:
          print('\nLa pagina '+page+' no es referenciada por ningun link')
          print('Definido en: ')
          for defi in list_of_pages[page]: 
            print('  ',defi)

    print("\nFunciones utilizadas:")    
    for functions in list_of_functions:
      print('  '+functions)

    print("\nVariables utilizadas:")    
    for var in conteo_de_variables:
      print('  '+var)
      if not conteo_de_variables[var].definition:
        print('¡Variable no definida!')
        print(conteo_de_variables[var])
      else:
        for decl in conteo_de_variables[var].declared_on:
          print('  '+decl)
      historia['_VAR_'][var] = conteo_de_variables[var].value

    historia = cleanDic(historia)

    if start_page:
      if start_page in historia:
        print('Fijando como pagina incial ',start_page)
        historia['_START_'] = start_page
      else:
        print('No se puede fijar como pagina incial ', start_page)

    with open('result.json', 'w') as fp:
        json.dump(historia, fp, separators=(',', ':'))
    
    file = open('result.json',"r")
    file_str = file.read()
    file.close()

    escribe_archivo_comprimido('juego/assets/data.dat',file_str)

  else:
    print("Entrada no valida, abortando!")

if __name__ == "__main__":
  run()