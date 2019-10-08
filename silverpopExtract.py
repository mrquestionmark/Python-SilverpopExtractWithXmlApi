import requests
from xml.etree import ElementTree

'''
Class XmlDictObject(dict)
    convert between xml string and dict
'''
class XmlDictObject(dict):
    """
    Adds object like functionality to the standard dictionary.
    """

    def __init__(self, initdict=None):
        if initdict is None:
            initdict = {}
        dict.__init__(self, initdict)
    
    def __getattr__(self, item):
        return self.__getitem__(item)
    
    def __setattr__(self, item, value):
        self.__setitem__(item, value)
    
    def __str__(self):
        if self.has_key('_text'):
            return self.__getitem__('_text')
        else:
            return ''

    @staticmethod
    def Wrap(x):
        """
        Static method to wrap a dictionary recursively as an XmlDictObject
        """

        if isinstance(x, dict):
            return XmlDictObject((k, XmlDictObject.Wrap(v)) for (k, v) in x.iteritems())
        elif isinstance(x, list):
            return [XmlDictObject.Wrap(v) for v in x]
        else:
            return x

    @staticmethod
    def _UnWrap(x):
        if isinstance(x, dict):
            return dict((k, XmlDictObject._UnWrap(v)) for (k, v) in x.iteritems())
        elif isinstance(x, list):
            return [XmlDictObject._UnWrap(v) for v in x]
        else:
            return x
        
    def UnWrap(self):
        """
        Recursively converts an XmlDictObject to a standard dictionary and returns the result.
        """

        return XmlDictObject._UnWrap(self)

def _ConvertDictToXmlRecurse(parent, dictitem):
    assert type(dictitem) is not type([])

    if isinstance(dictitem, dict):
        for (tag, child) in dictitem.items():
            if str(tag) == '_text':
                parent.text = str(child)
            elif type(child) is type([]):
                # iterate through the array and convert
                for listchild in child:
                    elem = ElementTree.Element(tag)
                    parent.append(elem)
                    _ConvertDictToXmlRecurse(elem, listchild)
            else:                
                elem = ElementTree.Element(tag)
                parent.append(elem)
                _ConvertDictToXmlRecurse(elem, child)
    else:
        parent.text = str(dictitem)
    
def ConvertDictToXml(xmldict):
    """
    Converts a dictionary to an XML string
    """

    roottag = list(xmldict)[0]
    root = ElementTree.Element(roottag)
    _ConvertDictToXmlRecurse(root, xmldict[roottag])

    return ElementTree.tostring(root)

def _ConvertXmlToDictRecurse(node, dictclass):
    nodedict = dictclass()
    
    if len(node.items()) > 0:
        # if we have attributes, set them
        nodedict.update(dict(node.items()))
    
    for child in node:
        # recursively add the element's children
        newitem = _ConvertXmlToDictRecurse(child, dictclass)
        if child.tag in nodedict:
            # found duplicate tag, force a list
            if type(nodedict[child.tag]) is type([]):
                # append to existing list
                nodedict[child.tag].append(newitem)
            else:
                # convert to list
                nodedict[child.tag] = [nodedict[child.tag], newitem]
        else:
            # only one, directly set the dictionary
            nodedict[child.tag] = newitem

    if node.text is None: 
        text = ''
    else: 
        text = node.text.strip()
    
    if len(nodedict) > 0:            
        # if we have a dictionary add the text as a dictionary value (if there is any)
        if len(text) > 0:
            nodedict['_text'] = text
    else:
        # if we don't have child nodes or attributes, just set the text
        nodedict = text
        
    return nodedict
        
def ConvertXmlToDict(root, dictclass=XmlDictObject):
    """
    Converts an XML file or ElementTree Element to a dictionary
    """

    # If a string is passed in, try to open it as a file
    if isinstance(root, str):
        import io
 
        root = io.StringIO(root)
        root = ElementTree.parse(root).getroot()
    elif not ElementTree.iselement(root):
        print('Expected ElementTree.Element or file path string')

    return dictclass({root.tag: _ConvertXmlToDictRecurse(root, dictclass)})


'''
main

1. login, get seesionID

<Envelope><Body>
<Login>
<USERNAME>rayb@mint.ca</USERNAME>
<PASSWORD>Hobbs437!</PASSWORD>
</Login>
</Body></Envelope>
'''
url = 'https://api5.silverpop.com/XMLAPI'
sessionid = None
url = '%s;jsessionid=%s' % (url,sessionid) 

xmlDic = {'Envelope':{'Body':None}}
xmlDic['Envelope']['Body'] = {
    'Login': {
        'USERNAME': 'rayb@mint.ca',
        'PASSWORD': 'Hobbs437!'
    }
}

# Convert to string
xml = ConvertDictToXml(xmlDic)

# Connect to silverpop and get our response
response = requests.post(url, data=xml,
                    headers={"Content-Type": "text/xml;charset=utf-8"})

# get sessionID
response = ConvertXmlToDict(response.content.decode('utf-8'), dict)
response = response.get('Envelope', {}).get('Body')

success = response.get('RESULT', {}).get('SUCCESS', 'false').lower()
success = False if success != 'true' and success != 'success' \
                                                                else True

sessionid = response.get('RESULT',{}).get('SESSIONID') if success else None

print(success)
print(sessionid)                    

'''

2. xml api call

<Envelope><Body>
<RawRecipientDataExport>
<EVENT_DATE_START>01/01/2008 00:00:00</EVENT_DATE_START>
<EVENT_DATE_END>01/31/2008 23:59:00</EVENT_DATE_END>
<LIST_ID>195986</LIST_ID>
<MOVE_TO_FTP/>
<INCLUDE_CHILDREN/>
<RETURN_MAILING_NAME/>
<RETURN_SUBJECT/>
<ALL_EVENT_TYPES/>
<EXCLUDE_DELETED/>
<COLUMNS>
<COLUMN>
<NAME>Custaccount</NAME>
</COLUMN>
<COLUMN>
<NAME>CustomerStream</NAME>
</COLUMN>
<COLUMN>
<NAME>CustomerStatus</NAME>
</COLUMN>
<COLUMN>
<NAME>LastSent</NAME>
</COLUMN>
<COLUMN>
<NAME>LastOpen</NAME>
</COLUMN>
<COLUMN>
<NAME>LastClick</NAME>
</COLUMN>
<COLUMN>
<NAME>Retail_date</NAME>
</COLUMN>
<COLUMN>
<NAME>Retail_location</NAME>
</COLUMN>
</COLUMNS>
</RawRecipientDataExport>
</Body></Envelope>
'''
import datetime

#yesterday from 00:00:00 to 23:59:59
yesterday = datetime.datetime.now() - datetime.timedelta(1)
startDate = yesterday.strftime('%m/%d/%Y')
endDate = startDate + ' 23:59:59'

xmlDic = {'Envelope':{'Body':None}}
xmlDic['Envelope']['Body'] = {
    'RawRecipientDataExport': {
        'EVENT_DATE_START': '03/28/2019',
        'EVENT_DATE_END': '03/28/2019 23:59:59',
        'LIST_ID':'195986',
        'MOVE_TO_FTP':'',
        'INCLUDE_CHILDREN':'',
        'RETURN_MAILING_NAME':'',
        'RETURN_SUBJECT':'',
        'ALL_EVENT_TYPES':'',
        'EXCLUDE_DELETED':'',
        'COLUMNS':{
            'COLUMN':[
                {'NAME':'Custaccount'},
                {'NAME':'CustomerStream'},
                {'NAME':'CustomerStatus'},
                {'NAME':'LastSent'},
                {'NAME':'LastOpen'},
                {'NAME':'LastClick'},
                {'NAME':'Retail_date'},
                {'NAME':'Retail_location'}
            ]
        }            
    }
}
# Convert to string
xml = ConvertDictToXml(xmlDic)


url = '%s;jsessionid=%s' % (url,sessionid) 

# Connect to silverpop and get our response
response = requests.post(url, data=xml,
                    headers={"Content-Type": "text/xml;charset=utf-8"})

response = ConvertXmlToDict(response.content.decode('utf-8'), dict)
response = response.get('Envelope', {}).get('Body')

success = response.get('RESULT', {}).get('SUCCESS', 'false').lower()
success = False if success != 'true' and success != 'success' \
                                                                else True
print(success)                    

'''

3. logout

<Envelope><Body>
<Logout/>
</Body></Envelope>
'''

xmlDic = {'Envelope':{'Body':None}}
xmlDic['Envelope']['Body'] = {
    'Logout': {
    }
}
# Convert to string
xml = ConvertDictToXml(xmlDic)

url = '%s;jsessionid=%s' % (url,sessionid) 

# Connect to silverpop and get our response
response = requests.post(url, data=xml,
                    headers={"Content-Type": "text/xml;charset=utf-8"})

response = ConvertXmlToDict(response.content.decode('utf-8'), dict)
response = response.get('Envelope', {}).get('Body')

success = response.get('RESULT', {}).get('SUCCESS', 'false').lower()
success = False if success != 'true' and success != 'success' \
                                                                else True
print(success)                    