import json

DATA = """[{                           
        "id": 3,            
        "name": "P50"       
},                          
{                           
        "id": 4,            
        "name": "P51"       
},                          
{                           
        "id": 6,            
        "name": "P53"       
},                          
{                           
        "id": 9,            
        "name": "port name" 
},                          
{                           
        "id": 10,           
        "name": "yeet"      
},                          
{                           
        "id": 11,           
        "name": "P03"       
},                          
{                           
        "id": 12,           
        "name": "P04"       
},                          
{                           
        "id": 13,           
        "name": "P05"       
},                          
{                           
        "id": 14,           
        "name": "P06"       
},                          
{                           
        "id": 15,           
        "name": "P07"       
},                          
{                           
        "id": 16,           
        "name": "P08"       
},                          
{                           
        "id": 17,           
        "name": "P09"       
},                          
{                           
        "id": 18,           
        "name": "P10"       
},                          
{                           
        "id": 19,           
        "name": "P11"       
},                          
{                           
        "id": 20,           
        "name": "P12"       
},                          
{                           
        "id": 21,           
        "name": "P13"       
},                          
{                           
        "id": 22,           
        "name": "P14"       
},                          
{                           
        "id": 23,           
        "name": "P15"       
},                          
{                           
        "id": 24,           
        "name": "P16"       
},                          
{                           
        "id": 25,           
        "name": "P17"       
},                          
{                           
        "id": 26,           
        "name": "P18"       
},                          
{                           
        "id": 27,           
        "name": "P19"       
},                          
{                           
        "id": 28,           
        "name": "P20"       
},                          
{                           
        "id": 29,           
        "name": "P21"       
},                          
{                           
        "id": 30,           
        "name": "P22"       
},                          
{                           
        "id": 31,           
        "name": "P23"       
},                          
{                           
        "id": 32,           
        "name": "P24"       
},                          
{                           
        "id": 33,           
        "name": "P25"       
},                          
{                           
        "id": 34,           
        "name": "P26"       
},                          
{                           
        "id": 35,           
        "name": "P27"       
},                          
{                           
        "id": 36,           
        "name": "P28"       
},                          
{                           
        "id": 37,           
        "name": "P29"       
},                          
{                           
        "id": 38,           
        "name": "P30"       
},                          
{                           
        "id": 39,           
        "name": "P31"       
},                          
{                           
        "id": 40,           
        "name": "P32"       
},                          
{                           
        "id": 41,           
        "name": "P33"       
},                          
{                           
        "id": 42,           
        "name": "P34"       
},                          
{                           
        "id": 43,           
        "name": "P35"       
},                          
{                           
        "id": 44,           
        "name": "P36"       
},                          
{                           
        "id": 45,           
        "name": "P37"       
},                          
{                           
        "id": 46,           
        "name": "P38"       
},                          
{                           
        "id": 47,           
        "name": "P39"       
},                          
{                           
        "id": 48,           
        "name": "P40"       
},                          
{                           
        "id": 49,           
        "name": "P41"       
},                          
{                           
        "id": 50,           
        "name": "P42"       
},                          
{                           
        "id": 51,           
        "name": "P43"       
},                          
{                           
        "id": 52,           
        "name": "P44"       
},                          
{                           
        "id": 53,           
        "name": "P45"       
},                          
{                           
        "id": 54,           
        "name": "P46"       
},                          
{                           
        "id": 55,           
        "name": "P47"       
},                          
{                           
        "id": 56,           
        "name": "P48"       
},                          
{                           
        "id": 64,           
        "name": "P49-1"     
},                          
{                           
        "id": 65,           
        "name": "P49-2"     
},                          
{                           
        "id": 66,           
        "name": "P49-3"     
},                          
{                           
        "id": 67,           
        "name": "P49-4"     
},                          
{                           
        "id": 2,            
        "name": "P52"       
},                          
{                           
        "id": 5,            
        "name": "P54-1"     
},                          
{                           
        "id": 7,            
        "name": "P54-2"     
},                          
{                           
        "id": 68,           
        "name": "P54-3"     
},                          
{                           
        "id": 69,           
        "name": "P54-4"     
}                           ]"""


def get_ports():
    return json.load(DATA)
