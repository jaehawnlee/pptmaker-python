import re
import json
import pprint

class Translator: 
    def __init__(self,data):
        self.data = data
        self.layer_pattern = re.compile('L[0-9]{1,3}')
        self.position_pattern = re.compile('\<[0-9]{1,3}\,[0-9]{1,3}\>')
        self.size_pattern = re.compile('\([0-9]{1,3}\,[0-9]{1,3}\)')

        self.text_pattern = re.compile('t=')
        self.picture_pattern = re.compile('p=')

    def __blind_mark(self, data) :
        temp_first_mark = [] # Parse to " ( " can not contain  " )
        temp_second_mark = [] # Parse to ' ( ' can contain " )

        parse_index_list = [] # result of parse index
        result_string_list = [] # result of parse string
        result_sentence = data
        
        for a in re.finditer('"', data) :
            temp_tuple = ('"',a.start())
            temp_first_mark.append(temp_tuple)

        for a in re.finditer("'", data) :
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
                            parse_index_list.append((temp_element[1],element[1]))
                            flag = False
                else :
                    temp_element = element
                    flag = True

        changed = 0
        for element in parse_index_list :
            temp_string = data[element[0]:element[1]+1]
            result_string_list.append(temp_string)
            result_sentence = result_sentence[:element[0]-changed] + '#' + result_sentence[element[1]+1 - changed:]
            changed = changed+len(temp_string)-1
            
        return (result_sentence, result_string_list)

    def __find_layer_info(self, data) :
        name = 'None' 
        position = (0,0)
        size = (10,10)
        
        search = self.layer_pattern.search(data)
        if search != None : name = search.group()
            
        search = self.position_pattern.search(data)
        if search != None : 
            _position = search.group().strip("<" ">").split(',')
            position = ( float(_position[0]), float(_position[1]) )
            
        search = self.size_pattern.search(data)
        if search != None : 
            _size =  search.group().strip("(" ")").split(',')
            size = (float(_size[0]), float(_size[1]))
        
        return (name,position,size)

    def __find_size_position_info(self, data) :
        position = (0,0)
        size = (10,10)
        
        search = self.position_pattern.search(data)
        if search != None : 
            _position = search.group().strip("<" ">").split(',')
            position = ( float(_position[0]), float(_position[1]) )
            
        search = self.size_pattern.search(data)
        if search != None : 
            _size =  search.group().strip("(" ")").split(',')
            size = (float(_size[0]), float(_size[1]))
        
        return {"size" : size ,"position" : position}

    def __find_type(self, data, text_data):
        size_postion_info = self.__find_size_position_info(data)

        if self.text_pattern.search(data) != None :
            dic = dict({"type" : "text"}, **size_postion_info)
            dic = dict(dic, **{"text_list" : self.__find_text_info(data,text_data)})
        elif self.picture_pattern.search(data) != None :
            dic = dict({"type" : "picture"}, **size_postion_info)
            dic = dict(dic, **{"path ": self.__find_picture_info(data)})
        else :
            dic = {"type" :"error", "detail" : "Object type error"}

        return dic

    # text 여러개면 text list 반환
    def __find_text_info(self, data, text_data):
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

    def __find_picture_info(self, data):
        path = re.search('\[p=([^)]+)\]', data).group().strip("[" "]").split('=')[1]
        return path

    def debug_print(self) :
        pprint.pprint(self.data)
    
    
    def translate(self) :
        total_layer_dic = { "layers" : [] } 
        
        blind_tuple = self.__blind_mark(self.data)
        blind_string = blind_tuple[0]
        
        split_dot_list = blind_string.split(sep='.')
        
        layer_index = []
    
        #Root layer로 부터 Layer를 나눈다
        for dot in split_dot_list :
            root_layer_name = ""
            split_layer_list = dot.split(sep='>>')
            
            #layer
            for layer in split_layer_list :
                if len(layer) > 0 :
                    split_object_list = layer.split(sep='in')
                    layer_info = self.__find_layer_info(split_object_list.pop(0))
                    
                    layer_name = layer_info[0]
                    this_layer_dic = {"name" : layer_name, "position" : layer_info[1], "size" : layer_info[2], "child_layer": []}
                    
                    if root_layer_name != "" :
                        layer_list =  total_layer_dic["layers"]
                        index = layer_index.index(root_layer_name)
                        
                        temp_list = layer_list[index]["child_layer"]
                    
                        if layer_name not in temp_list :
                            total_layer_dic["layers"][index]['child_layer'].append(layer_name)
                    
                    root_layer_name = layer_name
                    temp_object_list = []
                    
                    #object
                    for oject_list in split_object_list :
                        split_object = oject_list.split(sep='&')
                        
                        for object in split_object :
                            temp_object_list.append(self.__find_type(object,blind_tuple[1]))
                            
                    
                    if  layer_name not in layer_index:
                        info_dic = dict(this_layer_dic, **{"object_list" :temp_object_list})
                        total_layer_dic["layers"].append(info_dic)
                        layer_index.append(layer_name)
        
        return {"command" : total_layer_dic}     