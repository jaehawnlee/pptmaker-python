from doctest import Example
import os
import re
import json
import pprint


layer_pattern = re.compile('L[0-9]{1,3}')
position_pattern = re.compile('\<[0-9]{1,3}\,[0-9]{1,3}\>')
size_pattern = re.compile('\([0-9]{1,3}\,[0-9]{1,3}\)')

text_pattern = re.compile('t=')
picture_pattern = re.compile('p=')

def blind_mark(sentence) :
    temp_first_mark = []
    temp_second_mark = []

    result_index_list = []
    result_string_list = []
    
    for a in re.finditer('"',sentence) :
        temp_tuple = ('"',a.start())
        temp_first_mark.append(temp_tuple)

    for a in re.finditer("'",sentence) :
        temp_tuple = ("'",a.start())
        temp_second_mark.append(temp_tuple)
        
    if len(temp_first_mark) != 0 and len(temp_second_mark) != 0 :
        temp_list = temp_first_mark+temp_second_mark
        temp_list.sort(key=lambda x:x[1])
        
        flag = False
        temp_element = ''
        for element in temp_list :
            if flag :
                if temp_element[0] == element[0] :
                        result_index_list.append((temp_element[1],element[1]))
                        flag = False
            else :
                temp_element = element
                flag = True

    result_sentence = sentence
    
    changed = 0
    for element in result_index_list :
        temp_string = sentence[element[0]:element[1]+1]
        result_string_list.append(temp_string)
        result_sentence = result_sentence[:element[0]-changed] + '#' + result_sentence[element[1]+1 - changed:]
        changed = changed+len(temp_string)-1
        
    return (result_sentence, result_string_list)

def find_layer_info(layer) :
    name = 'None' 
    position = (0,0)
    size = (10,10)
    
    search = layer_pattern.search(layer)
    if search != None : name = search.group()
        
    search = position_pattern.search(layer)
    if search != None : 
        _position = search.group().strip("<" ">").split(',')
        position = ( float(_position[0]), float(_position[1]) )
        
    search = size_pattern.search(layer)
    if search != None : 
        _size =  search.group().strip("(" ")").split(',')
        size = (float(_size[0]), float(_size[1]))
    
    return (name,position,size)

def find_size_position_info(data) :
    position = (0,0)
    size = (10,10)
    
    search = position_pattern.search(data)
    if search != None : 
        _position = search.group().strip("<" ">").split(',')
        position = ( float(_position[0]), float(_position[1]) )
        
    search = size_pattern.search(data)
    if search != None : 
        _size =  search.group().strip("(" ")").split(',')
        size = (float(_size[0]), float(_size[1]))
    
    return {"size" : size ,"position" : position}

def find_type(data, text_data):
    
    size_postion_info = find_size_position_info(data)

    if text_pattern.search(data) != None :
        dic = dict({"type" : "text"}, **size_postion_info)
        dic = dict(dic, **{"text_list" : find_text_info(data,text_data)})
    elif picture_pattern.search(data) != None :
        dic = dict({"type" : "picture"}, **size_postion_info)
        dic = dict(dic, **{"path ": find_picture_info(data)})
    else :
        dic = {"type" :"error", "detail" : "Object type error"}

    return dic

# text 여러개면 text list 반환
def find_text_info(data, text_data):
    text = data.split('=')[1].strip("[""]")
    text = text.replace(" ","")
    
    config_list = []
    reuslt_list = []
    changed = 0
    
    temp_string = text

    for a in re.finditer('\(([^)]+)\)', text) :
        config_list.append(a.group())
        temp_string = temp_string[:a.start()-changed] + '$' + temp_string[a.end() - changed:]
        changed = changed+len(a.group())-1
    
    index = -1
    for c in temp_string :
        if c == '#' :
            index = index + 1
            reuslt_list.append({'text' : text_data.pop(0) })        
        elif c == '$':
            reuslt_list[index]['config'] = config_list.pop(0).strip("(" ")")
        elif c == '/':
            reuslt_list[index]['text'] = reuslt_list[index]['text']+"\n"
            
    return reuslt_list

def find_picture_info(data):
    path = re.search('\[p=([^)]+)\]', data).group().strip("[" "]").split('=')[1]
    return path

#add 
example0 = "<0,0>(20,20)L1 in <0,0>(5,5)[p=키워드] & <0,0>(5,5)[t= \"나는\"(서식1)/ '\"[나는]\"' \" L1\"(서식2) \" 이다.\"(서식1)]."\
           "<5,5>(10,10)L2 >> <2,2>(5,5)L3 in <0,0>(5,5)[t= \"나는\"(서식1)/ '\"[나는]\"' \" L3 \"(서식2) \" 이다.\"(서식1)]."\
           "<20,20>(10,10)L5 in <0,0>(5,5)[p=키워드] & <0,0>(5,5)[t= \"나는\"(서식1)/ '\"[나는]\"' \" L5 \"(서식2) \" 이다.\"(서식1)]."\
           "L1 >> L2." \
                
def translate(data) :
    total_layer_dic = {}
       
    blind_tuple = blind_mark(example0)
    blind_string = blind_tuple[0]
    
    split_dot_list = blind_string.split(sep='.')
 
    #Root layer로 부터 Layer를 나눈다
    for dot in split_dot_list :
        root_layer_name = ""
        split_layer_list = dot.split(sep='>>')
        
        #layer
        for layer in split_layer_list :
            if len(layer) > 0 :
                split_object_list = layer.split(sep='in')
                layer_info = find_layer_info(split_object_list.pop(0))
                
                layer_name = layer_info[0]
                this_layer_dic = {"position" : layer_info[1], "size" : layer_info[2], "child_layer": []}
                
                if root_layer_name != "" :
                    temp_list = total_layer_dic[root_layer_name]["child_layer"]
                   
                    if layer_name not in temp_list :
                         total_layer_dic[root_layer_name]['child_layer'].append(layer_name)
                
                root_layer_name = layer_name
                temp_object_list = []
                
                #object
                for oject_list in split_object_list :
                    split_object = oject_list.split(sep='&')
                    
                    for object in split_object :
                        temp_object_list.append(find_type(object,blind_tuple[1]))
                        
                
                if total_layer_dic.get(layer_name) == None :
                    info_dic = dict(this_layer_dic, **{"object_list" :temp_object_list})
                    total_layer_dic[layer_name] = info_dic
    
    return total_layer_dic     

total_layer_dic = translate(example0)

with open('data.json','w') as f:
  json.dump(total_layer_dic,f, indent=2, ensure_ascii = False)
