from lxml import etree, objectify
import re
import copy
from pprint import pprint

import glob,string
from itertools import product,chain
import csv,os,datetime
from os import path
from os.path import basename,splitext


global return_lst,rtrn_dict
return_lst = []
rtrn_dict = {}

def sort_nodes(node) :
    node[:] = sorted(node,key = lambda leaf_node : 0 if leaf_node.getchildren() == [] else 1)
    return

def sort(node):
    """ Sort nodes so that nodes with no children are at the beggining"""
    if len(node) != 0 :
        for child in node:
            sort(child)
        #sort all child elments based on the presence of child nodes
        sort_nodes(node)

def removenamespaces(tree):
    for elem in tree.iter():
        if not hasattr(elem.tag, 'find'): continue  # (1)
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i + 1:]
    objectify.deannotate(tree.getroot(), cleanup_namespaces=True)

def getformattedxpath(xpath) :
    return re.sub(r'\[\d\]', '', xpath)

def getfrmtxpathtree(node,tree) :
    xpath = tree.getpath(node)
    return getformattedxpath(xpath)

def getonenodeabove(xpath) :
    return xpath.rsplit('/',1)[0]


def getlistofleafnodes(xpth_lst) :
    return_lst = []
    sorted_lst = map(getonenodeabove,xpth_lst)
    sorted_lst = sorted(set(sorted_lst))
    if len(sorted_lst) == 1 :
        return sorted_lst
    else :
        for cntr in range(len(sorted_lst)) :
            if cntr != 0 :
                if set(sorted_lst[cntr-1].split('/')) - set(sorted_lst[cntr].split('/')) :
                    return_lst.append(sorted_lst[cntr-1])
                    # add the last element to the list if it is different
                    if cntr == len(sorted_lst) -1 :
                        return_lst.append(sorted_lst[cntr])
        return return_lst

def getdeepestchildnodes(tree) :
    temp_list = list()
    for element in tree.iter():
        if element.text is not None and element.text.strip():
            temp_list.append(getfrmtxpathtree(element,tree))
    return getlistofleafnodes(temp_list)


def traverseNodes(node,node_lst,tree,filter_list) :
    frmtd_xpath = getfrmtxpathtree(node,tree)
    if len(node) != 0:
        node_lst = copy.deepcopy(node_lst)
        for child in node:
            traverseNodes(child,node_lst,tree,filter_list)

        # after traversing all the children             
    elif node.text is not None and node.text.strip():
        if getfrmtxpathtree(node,tree) in filter_list :
            node_lst.append({frmtd_xpath:node.text})
            tst = tree.getpath(node)

            if not rtrn_dict.get(getonenodeabove(tst)) :
                rtrn_dict[getonenodeabove(tst)] = node_lst
    return rtrn_dict

def filternodes(node_lst, filterlist):
    rtrn_grp_dict = dict()
    for node in node_lst:
        group_name = getonenodeabove(node[0])
        if group_name in filterlist :
            if rtrn_grp_dict.get(group_name) :
                rtrn_grp_dict.get(group_name).append(node)
            else :
                rtrn_grp_dict[group_name] = [node]
    return rtrn_grp_dict


def filternodes_v2(node_lst, filterlist):
    rtrn_grp_dict = dict()
    for node in node_lst:
        if getformattedxpath(node) in filterlist :
            if rtrn_grp_dict.get(node) :
                rtrn_grp_dict.get(node).append(node_lst[node])
            else :
                rtrn_grp_dict[node] = node_lst[node]
    return rtrn_grp_dict

def group_elements(element_dict) :
    return_grouped_dict = {}
    for keys in element_dict :
        if return_grouped_dict.get(getformattedxpath(keys)) :
            return_grouped_dict.get(getformattedxpath(keys)).append(element_dict[keys])
        else :
            return_grouped_dict[getformattedxpath(keys)] = [element_dict[keys]]
    return return_grouped_dict



xml_dict = dict()
time_stamp = datetime.datetime.now().strftime("%d_%b_%Y-%I-%M-%S_%p")
print("Execution started: "+datetime.datetime.now().strftime("%d-%b-%Y %I:%M:%S %p"))

for input_file in glob.glob(".\\input\\*.xml") :
    print(input_file)
    global return_lst,rtrn_dict
    return_lst = []
    rtrn_dict = {}
    with open(input_file, 'rb') as f:
        parser = etree.XMLParser(remove_blank_text=True)
        #blank the tree and then proceed
        tree = ""

        tree = etree.parse(f, parser=parser)
        

        removenamespaces(tree)

        # pprint(traverseNodes(tree.getroot(),[],tree),width=20000)
        # pprint(getdeepestchildnodes(tree),width=200)

        sort(tree.getroot())

        for filename in glob.glob(".\\parameters\\*") :
            filehandle = open(filename,'rb')
            # remove non-printable characters
            filter_list = [ filter(lambda x: x in string.printable, linestring.strip()) for linestring in filehandle.readlines()]
            # pprint(getlistofleafnodes(filter_list))
            #print("----------------")
            #pprint(traverseNodes(tree.getroot(),[],tree,filter_list))
            # pprint(group_elements(filternodes_v2(traverseNodes(tree.getroot(),[],tree,filter_list),getlistofleafnodes(filter_list))))

            
            listtobemultiplied = group_elements(filternodes_v2(traverseNodes(tree.getroot(),[],tree,filter_list),getlistofleafnodes(filter_list))).values()
            muliplied_list = list(product(*listtobemultiplied))

            result_set = []
            for x in muliplied_list :
                temp_list = []
                temp_set = set()
                temp_tuple = tuple()
                for y in chain.from_iterable(x) :
                    # print(y)
                    temp_set.add(tuple(y.items()))
                for t in temp_set :
                    temp_list.append(t[0])
                result_set.append(dict(temp_list))
                # print("===="*10)

            
            # get the directory aboe the paramfolder
            above_path =  path.abspath(path.join(filename ,"../.."))
            #get the filename only without folders just filename.txt
            filename = os.path.basename(filename)
            #remove extension
            filename = os.path.splitext(filename)[0]
            filename = above_path+"\\output\\"+time_stamp+"\\"+filename+".csv"

            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

            if os.path.exists(filename):
                append_write = 'ab' # append if already exists
            else:
                append_write = 'wb' # make a new file if not

            fieldnames =result_set[0].keys()
            with open(filename, append_write) as csvfile:
                writer = csv.DictWriter(csvfile,fieldnames=filter_list) 

                if append_write != 'ab' :
                    #x paths
                    writer.writeheader()
                    # field names with only the last part     
                    writer.writerow({k:k.rsplit('/',1)[1] for k in  filter_list })

                for x in result_set :
                    # print(x)
                    writer.writerow(x)

print("Execution Completed: "+datetime.datetime.now().strftime("%d-%b-%Y %I:%M:%S %p"))
