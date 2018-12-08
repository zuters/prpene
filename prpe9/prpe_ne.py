    #!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Jānis Zuters
# PRPE technical version 9

#=============================================================================

import codecs
import sys
from collections import Counter
from copy import deepcopy
from numpy import argmin

goodroots = Counter()
badroots = {}
goodprefixes = Counter()
badprefixes = {}
goodpostfixes = Counter()
badpostfixes = {}

premaxlen = 8
postmaxlen = 7
minrootlen = 2
minpreflen = 2

def isUlower(word):
    return len(word)>=2 and word[0:1].isupper() and word[1:].islower() and word.isalpha()

def isUlower2(word):
    return len(word)>=2 and word[0:1].isupper() and word[1:2].islower() and word.isalpha()

def processUlower(word):
    if isUlower(word):
        return word.lower()
    else: return word

def processUlower2(word):
    if isUlower2(word):
        return word[0].lower()+word[1:]
    else: return word

def spos(pos,L):
    return (pos+0.5)/L

def sposback(sps,L):
    return round(sps*L-0.5)

def words_match(w1,w2):
    if len(w1)<len(w2):
        ww = w1
        w1 = w2
        w2 = ww
    L1 = len(w1)
    L2 = len(w2)
    i2 = 0
    ret = 0
    for i1 in range(L1):
        sps1 = spos(i1,L1)
        for ii2 in range(i2,min(sposback(sps1,L2)+3,L2)):
            if w1[i1]==w2[ii2]:
                i2 = ii2+1
                ret+=1
                break
    return ret / L1

def read_parallel_lines(finname1,finname2,fin1,fin2,startpos,lmaxcount=None,stopatend=True):
    lcount = 0
    repo1 = []
    repo2 = []
    stop = False
    eof = False
    while not stop:
        if startpos[0]==0:
            fin1 = codecs.open(finname1, 'r', encoding='utf-8')
            fin2 = codecs.open(finname2, 'r', encoding='utf-8')
#        print(startpos)
        fin1.seek(startpos[0])
        fin2.seek(startpos[1])
        cline = 0
        line1 = fin1.readline()
        while line1 != '':
            line2 = fin2.readline()
            # except extra line which is subject to check for eof
            if lmaxcount is None or lcount<lmaxcount:
                repo1.append(line1)
                repo2.append(line2)
            lcount+=1
            if lmaxcount is not None and lcount<=lmaxcount:
                startpos[0]+=len(line1.encode('utf-8'))
                startpos[1]+=len(line2.encode('utf-8'))
            # lmaxcount+1: to check for eof
            if lmaxcount is not None and lcount>=lmaxcount+1:
                stop = True
                break
            cline += 1
            line1 = fin1.readline()
        if lmaxcount is None:
            stop = True
        if line1=="": # eof check
            fin1.close()
            fin2.close()
            eof = True
            startpos[0] = 0
            startpos[1] = 0
            if stopatend:
                stop = True
    return repo1,repo2,eof,fin1,fin2

def preprocess_sentence_alpha_pairs(sentence1,tolower):        
    if tolower:
        sentence1 = sentence1.lower()
    s1 = [word1 for word1 in sentence1.split()[1:] if word1.isalpha()]
    return s1

def collect_ne_pairs(cname1,cname2,fnename1,fnename2,fnename="",alphaonly=1,tolower=False):
    eof = False
    maxdnum = None
    dnum = 0
    fin1 = None
    fin2 = None
    startline = [0,0]
    fne1 = codecs.open(fnename1, 'w', encoding='utf-8')
    fne2 = codecs.open(fnename2, 'w', encoding='utf-8')
    if fnename != "":
        fne = codecs.open(fnename, 'w', encoding='utf-8')
    ii = 1
    while not eof and (maxdnum is None or dnum < maxdnum):
        dnum += 1
        print('Data:',dnum)
        repo1,repo2,eof,fin1,fin2 = read_parallel_lines(
                cname1,cname2,fin1,fin2,startline,lmaxcount=5000,stopatend=True)
        i = 0
        for sentence1 in repo1:
            sentence2 = repo2[i]
            s1 = preprocess_sentence_alpha_pairs(sentence1,tolower)
            s2 = preprocess_sentence_alpha_pairs(sentence2,tolower)
#            if ii==1335:
#                print(sentence1)
#                print(sentence2)
#                print(s1)
#                print(s2)
            ul1 = 0
            ul2 = 0
            ww1=""
            ww2=""
            for w1 in s1:
                if isUlower2(w1):
                    ul1 += 1
                    ww1 = w1
            for w2 in s2:
                if isUlower2(w2):
                    ul2 += 1
                    ww2 = w2
            if ul1==1 and ul2==1:
                if words_match(ww1,ww2)<0.3:
                    pass
                else:
                    print (ii,ww1,file=fne1)
                    print (ii,ww2,file=fne2)
                    if fnename != "":
                        print (ii,ww1,ww2,file=fne)
            i+=1
            ii+=1

#        print("Pairs ne 1", pairs_ne1)
    fin1.close()
    fin2.close()
    fne1.close()
    fne2.close()
    if fnename != "":
        fne.close()

def search_codetree(tword,codetree):
    """ Stored in codetree with non-zero value in the terminal node
    """
    pos = 0
    while True:
        s = tword[pos]
        if s not in codetree:
            return 0
        elif pos==len(tword)-1:
            return codetree[s][0]
        else:
            pos += 1
            codetree = codetree[s][1]
    
def search_codetree_hasleftsub(tword,codetree):
    """ Stored in codetree with non-zero value in any except the terminal node
    """
    pos = 0
    while True:
        s = tword[pos]
        if s not in codetree:
            return 0
        elif codetree[s][0]>0:
            return codetree[s][0]
        elif pos==len(tword)-1:
            return 0
        else:
            pos += 1
            codetree = codetree[s][1]
    
def search_codetree_isleftsub(tword,codetree):
    """ Stored in codetree having any value terminal node (i.e., reaching terminal node)
    """
    pos = 0
    while True:
        s = tword[pos]
        if s not in codetree:
            return 0
        elif pos==len(tword)-1:
            return 1
        else:
            pos += 1
            codetree = codetree[s][1]
    
def add_to_codetree(tword,codetree,freq=1):
    """ Adds word to tree structure - one node per symbol
    """
    unique=0
    for pos in range(len(tword)):
        s = tword[pos]
        if s not in codetree:
            codetree[s] = [0,{}]
            unique+=1
        codetree[s][0] += freq
        codetree = codetree[s][1]
    return unique

def add_to_vocab_multi(word,vocab,freq):
    for pos in range(len(word)):
        if not word[pos].isalpha(): return
        vocab[word[:pos+1]] += freq

def add_to_vocab_multi_reverse(word,vocab,postmaxlen,minrootlen,freq):
    """ Adds one tuple-word to tree structure - one node per symbol
        word end in the tree characterized by node[0]>0
    """
    pos = 0
    while pos<len(word)-minrootlen and pos<postmaxlen:
        vocab[word[:pos+1]] += freq
        pos+=1

def add_to_codetree_terminal(tword,codetree,freq=1):
    """ Adds word to tree structure - one node per symbol
        word end in the tree characterized by node[0]>0
    """
    for pos in range(len(tword)):
        s = tword[pos]
        if s not in codetree:
            codetree[s] = [0,{}]
        if pos==len(tword)-1:
            codetree[s][0] = freq
        else:
            codetree = codetree[s][1]

def read_codetree(datafile,reverse=False):
    codetree = {}
    for line in datafile:
        item = line.split()
        word = item[0]
        if reverse: word=word[::-1]
        if len(item)>1:
            num = int(item[1])
        else:
            num = 1
        add_to_codetree_terminal(word,codetree,num)
    return codetree

def read_vocabulary(vocabfile,reverse=False):
    vocab = Counter()
    rcounter = 999999999
    for line in vocabfile:
        item = line.split()
        word = item[0]
        if reverse: word=word[::-1]
        if len(item)>1:
            num = int(item[1])
        else:
            num = rcounter
            rcounter-=1
        vocab[word] = num
    return vocab

def read_nent(vocabfile):
    vocab = {}
    for line in vocabfile:
        item = line.split()
        num = int(item[0])
        word = item[1]
        vocab[num] = word
    return vocab

def read_nent_int(vocabfile):
    vocab = {}
    for line in vocabfile:
        item = line.split()
        num = int(item[0])
        word = int(item[1])
        vocab[num] = word
    return vocab

def extract_vocabulary(infile):
    vocab = Counter()
    for line in infile:
        for word in line.split():
#            word = processMeta(word)
            word = processUlower(word)
            vocab[word] += 1
    return vocab

def save_vocabulary(vocabfile,vocab,order=False,reverseorder=True,alphaonly=False,maxcount=None,vocabout=None):
    cnt = 0
    if order:
        for item in sorted(vocab.items(),key=lambda x: x[1],reverse=reverseorder):
            if maxcount is not None and cnt==maxcount: return
            if not alphaonly or item[0].isalpha():
                vocabfile.write(u"{0} {1}\n".format(item[0],item[1]))
                if vocabout is not None: vocabout[item[0]]=item[1]
                cnt+=1
    else:
        for item in vocab.items():
            if maxcount is not None and cnt==maxcount: return
            if not alphaonly or item[0].isalpha():
                vocabfile.write(u"{0} {1}\n".format(item[0],item[1]))
                if vocabout is not None: vocabout[item[0]]=item[1]
                cnt+=1

def register_subwords(infile,premaxlen,postmaxlen,minrootlen,isvocabin=False,vocabout=None,rawprefixfile=None,rawpostfixfile=None,loadrawfile=False,freqnotrank=False):
    rawprecodetree = {}
    rawpostcodetree = {}
    if isvocabin:
        vocab = read_vocabulary(infile)
    else:
        vocab = extract_vocabulary(infile)
    if loadrawfile:
        rawprevocab = read_vocabulary(rawprefixfile)
        rawpostvocab = read_vocabulary(rawpostfixfile)
    else:
        rawprevocab = Counter()
        rawpostvocab = Counter()
        for item in vocab.items():
            word = item[0]
            freq = item[1]
            preword =word[:premaxlen]
            add_to_vocab_multi(preword,rawprevocab,freq)
            add_to_vocab_multi_reverse(word[::-1],rawpostvocab,postmaxlen,minrootlen,freq)
#    funique = len(rawprevocab)
#    runique = len(rawpostvocab)
    prevfreq = -1
    num = 0
    for item in sorted(rawprevocab.items(),key=lambda x: x[1],reverse=True):
        word = item[0]
        freq = item[1]
        if freqnotrank:
            num = freq
        else:
            if freq!=prevfreq: num+=1
        add_to_codetree_terminal(word,rawprecodetree,num)
        if not loadrawfile and rawprefixfile:
            rawprefixfile.write(" {0} {1}\n".format(word,num))
        prevfreq = freq
    prevfreq = -1
    num = 0
    for item in sorted(rawpostvocab.items(),key=lambda x: x[1],reverse=True):
        word = item[0]
        freq = item[1]
        if freqnotrank:
            num = freq
        else:
            if freq!=prevfreq: num+=1
#        if freq!=prevfreq: num+=1 # tmp not used
        add_to_codetree_terminal(word,rawpostcodetree,num)
        if not loadrawfile and rawpostfixfile:
            rawpostfixfile.write(" {0} {1}\n".format(word,num))
        prevfreq = freq
        
#    print("vocab",len(vocab))
#    print("funique",funique)
#    print("runique",runique)
    if vocabout is not None:
        save_vocabulary(vocabout,vocab,True)
    return rawprecodetree,rawpostcodetree,vocab,rawprevocab
        

def print_subwords(infile,codefile,n,reverse=False):
    ngrams = Counter()
    vocab = extract_vocabulary(infile)
    # register (left or right) n-grams
    for word in vocab.keys():
        if reverse:
            if len(word)>=n+1: # right without first
                ngrams[word[-n:]] += 1
        else:
            if len(word)>=n: # left
                ngrams[word[:n]] += 1
    # count and print (left or right) n-grams
    print(len(ngrams))
    for item in sorted(ngrams.items(),key=lambda x: x[1],reverse=True):
        codefile.write("{0} {1}\n".format(item[0],item[1]))
    
def add_subwords(codetree,tword,pos,subgraph):
    pos0 = pos
    while pos < len(tword):
        s = tword[pos]
        if s not in codetree:
            return
        else:
            if codetree[s][0]>0:
                posnext = pos + 1
                if posnext not in subgraph[pos0]:
                    subgraph[pos0][posnext] = 0
                subgraph[pos0][posnext] = max(subgraph[pos0][posnext],codetree[s][0])
            pos += 1
            codetree = codetree[s][1]

def add_subwords_reverse(codetree,tword,pos,subgraph):
    posright = pos
    while pos >= 2:
        s = tword[pos-1]
        if s not in codetree:
            return
        else:
            if codetree[s][0]>0:
                posleft = pos - 1
                if posright not in subgraph[posleft]:
                    subgraph[posleft][posright] = 0
                subgraph[posleft][posright] = max(subgraph[posleft][posright],codetree[s][0])
            pos -= 1
            codetree = codetree[s][1]

def create_subgraph(precodetree,postcodetree,tword):
    subgraph = [{} for i in range(len(tword))]
    for pos in range(0,len(subgraph)-1):
        add_subwords(precodetree,tword,pos,subgraph)
#    for pos in range(len(subgraph),0,-1):
#        add_subwords_reverse(postcodetree,tword,pos,subgraph)
    add_subwords_reverse(postcodetree,tword,len(subgraph),subgraph)
    return subgraph

def analyze_subgraph(subgraph,word,track="",pos=0,freq="",leng=0):
    if pos==len(word):
        if leng<=3:
            print(track,freq)
    else:
        if len(track)>0:
            track += "-"
            freq+=" "
        for nextpos in subgraph[pos]:
            nextfreq = subgraph[pos][nextpos]
            analyze_subgraph(subgraph,word,track+word[pos:nextpos],nextpos,freq+str(nextfreq),leng+1)
            
# === Generic heuristics BEGIN            
            
nonprefixes_dict = {}        
            
vowels=u"aāeēiīoōuūy";
vowdict={}
for v in vowels:
    vowdict[v]=1
    
def containsvowel(word):
    for s in word:
        if s in vowdict: return True
    return False

def is_good_part_generic(part,word=''):
    return (
        part.isalpha()
        and part.islower()
        and containsvowel(part)
    )
            
# === Generic heuristics END

# === English specific heuristics BEGIN    

nonprefixes_en = ["non","un","im"]
nonprefixes_dict_en={}
for v in nonprefixes_en:
    nonprefixes_dict_en[v]=1
            
def is_good_root_en(part,word):
    return len(part)>2 and is_good_part_generic(part)

def is_good_postfix_en(part):
    if len(part)<=2:
        return is_good_ending_en(part) or part in ["ly"]
    elif len(part)>5:
        return False
    else:
        if part in ["ment","ling","ness"]: return True
        if not is_good_part_generic(part):
            return False
        if part[0] not in vowdict:
            return False
        return True

def is_good_ending_en(part):
    return part in ["s","ed","e","y","es","er","ies"]
    
def is_good_ending_ne_en(part):
    return False
    
def is_good_prefix_en(part):
    return is_good_part_generic(part)

# === English specific  heuristics END

# === Latvian specific heuristics BEGIN            
            
nonprefixes_lv = ["ne"]
nonprefixes_dict_lv={}
for v in nonprefixes_lv:
    nonprefixes_dict_lv[v]=1
            
vowels_not_o=u"aāeēiīōuūy";
vowdict_not_o={}
for v in vowels_not_o:
    vowdict_not_o[v]=1

badrootstart_lv = "cčjlļmnņr"    
badrootstart_dict_lv={}
for v in badrootstart_lv:
    badrootstart_dict_lv[v]=1
badrootend_lv = ["šs"]
badrootend_dict_lv={}
for v in badrootend_lv:
    badrootend_dict_lv[v]=1

def is_good_root_lv(root,word):
#    if len(root)<=2: return False
    if root[-1] in vowdict_not_o: return False
    if root[-1] == "o" and len(root)<4: return False
    if root[-2] in ['p','t'] and root[-1] not in ['l','r','j','n','t','s','o']: return False
    if len(root)==len(word) and len(root)<4: return False
    if root[1] not in vowdict and root[0] in badrootstart_dict_lv: return False
    if root[-2:] in badrootend_dict_lv: return False
    return is_good_part_generic(root)

def is_good_postfix_lv(part):
    if len(part)==1:
        if part in vowdict: return True
        elif part in ["t","s","š"]: return True
        else: return False
    else:
        if not is_good_part_generic(part):
            return False
        if part[-1] not in vowdict and part[-1] not in ["m","s","š","t"]: return False
        if len(part)==2:
             # postfixes of length 2 should contain vowel at position 0 (LATVIAN?)
            if part[0] not in vowdict or part[-1]=="o":
                return False
        else: # postfix length 3 or more
            if part=="sies": return True 
            if part=="ties": return True 
            if part[:3]=="šan": return True 
            if part[:3]=="nīc": return True 
            if part[:4]=="niek": return True 
            if part[:4]=="niec": return True 
            if part[:4]=="nieč": return True 
            if not containsvowel(part[0]):
                return False
    return True

def is_good_ending_lv(part):
    """ Is ending in Latvian, assuming it is good postfix
    """
    if len(part)>4: return False
    elif len(part)==4:
        if part in ["sies","ties"]: return True
    elif len(part)==3:
        if part in ["iem","ies","ais"]: return True
    elif len(part)==2:
        if part[-1]=="š": return False
        elif part[0] in vowdict and part[1] in vowdict:
            if part in ["ai","ie","ei"]: return True
            else: return False
        elif part in ["om","ūs","et","ut","ūt"]: return False
        else: return True
    else: # length = 1
        return True
    return False
    
def is_good_ending_ne_lv(part):
    if len(part)>3: return False
    elif len(part)==3:
        if part in ["iem","ais"]: return True
        else: return True
    elif len(part)==2:
        if part[-1] in["š","t"]: return False
        elif part[0] in vowdict and part[1] in vowdict:
            if part in ["ai","ie","ei"]: return True
            else: return False
        elif part in ["om","ūs"]: return False
        else: return True
    else: # length = 1
        if part in ["t","o","y"]: return False
        else: return True
    
def is_good_prefix_lv(part):
    return is_good_part_generic(part)

# === Latvian specific heuristics END

def add_heuristics(lang=''):
    lang = lang.lower()
    global is_good_prefix
    global is_good_root
    global is_good_postfix
    global is_good_ending
    global is_good_ending_ne
    global nonprefixes_dict
    if lang=='lv':
        is_good_prefix = is_good_prefix_lv
        is_good_root = is_good_root_lv
        is_good_postfix = is_good_postfix_lv
        is_good_ending = is_good_ending_lv
        is_good_ending_ne = is_good_ending_ne_lv
        nonprefixes_dict = nonprefixes_dict_lv
    elif lang=='en':
        is_good_prefix = is_good_prefix_en
        is_good_root = is_good_root_en
        is_good_postfix = is_good_postfix_en
        is_good_ending = is_good_ending_en
        is_good_ending_ne = is_good_ending_ne_en
        nonprefixes_dict = nonprefixes_dict_en
    else:
        lang = 'unspecified'
        is_good_prefix = is_good_prefix_en
        is_good_root = is_good_root_en
        is_good_postfix = is_good_postfix_en
        is_good_ending = is_good_ending_en
        is_good_ending_ne = is_good_ending_ne_en
        nonprefixes_dict = nonprefixes_dict_en
    sys.stderr.write('Heuristics: {0}\n'.format(lang))

def analyze_prefixes(prefsource,rootsource,vocab,rawprevocab,preffile=None,loadfile=False):
    """ Collect candidate prefixes
    """
    prefixes = Counter()
    if loadfile:
        if preffile is not None:
            for line in preffile:
                entry = line.split()
                prefixes[entry[0]] = int(entry[1])
    else:
#        TEST=0
#        CNT=0
        for prefix in goodprefixes:
            prefixes[prefix] = goodprefixes[prefix]
        preflen1 = minpreflen
        preflen2 = 4
        rootlen1 = 4
        rootlen2 = 7
        for item in vocab.items():
            word = item[0]
#            freq = item[1]
            preftree = prefsource
            for p in range(1,preflen2+1):
                if p+rootlen1>len(word): break
                ps = word[p-1]
                if ps not in preftree: break
                elif preftree[ps][0]>0 and p>=preflen1:
                    prefix = word[:p]
                    if is_good_prefix(prefix) and search_codetree(prefix,badprefixes)==0:
                        roottree = rootsource
                        for r in range(1,rootlen2+1):
                            pr = p+r
                            if pr>len(word): break
                            prs = word[pr-1]
                            if prs not in roottree: break
#                            elif not freqnotrank: # ranking
#                                if prefixes[prefix]==0 or roottree[prs][0]<prefixes[prefix]:
#                                    prefixes[prefix]=roottree[prs][0]
#                            elif roottree[prs][0]>0 and r>=rootlen1 and is_good_root(word[p:pr],word): # frequence
#                                prefixes[prefix]+=roottree[prs][0]
                            root=word[p:pr]
                            if r>=rootlen1 and roottree[prs][0]>0 and is_good_root(root,word):
                                prefixes[prefix]+=rawprevocab[root]
                            roottree = roottree[prs][1]
                preftree = preftree[ps][1]
        if preffile is not None:
            for item in sorted(prefixes.items(),key=lambda x: x[1],reverse=True):
                preffile.write(" {0} {1}\n".format(item[0],item[1]))
#        print("CNT",CNT,TEST)
    return prefixes
        
longenoughpplen = 5
ppregbase = 3

def analyze_postfixes(rootsource,postsource,vocab,rawprevocab,postfile=None,sufffile=None,endfile=None,loadfile=False):
    """ Collect candidate postfixes, suffixes, endings
    """
    postfixes = Counter()
    suffixes = Counter()
    endings = Counter()
    if loadfile:
        if postfile is not None:
            for line in postfile:
                entry = line.split()
                postfixes[entry[0]] = int(entry[1])
        if sufffile is not None:
            for line in sufffile:
                entry = line.split()
                suffixes[entry[0]] = int(entry[1])
        if endfile is not None:
            for line in endfile:
                entry = line.split()
                endings[entry[0]] = int(entry[1])
    else:
        for postfix in goodpostfixes:
            postfixes[postfix] = goodpostfixes[postfix]
        postlen2 = 7
        rootlen1 = 4
        rootlen2 = 7
        for item in vocab.items():
            word = item[0]
#            freq = item[1]
            posttree = postsource
            for p in range(1,postlen2+1):
                if p+rootlen1>len(word): break
                ps = word[-p]
                if ps not in posttree: break
                elif posttree[ps][0]>0:
                    postfix = word[-p:]
                    if is_good_postfix(postfix) and search_codetree(postfix,badpostfixes)==0:
                        for rootlen in range(rootlen1,1+min(rootlen2,len(word)-p)):
                            roottree = rootsource
                            for r in range(rootlen,0,-1):
                                pr = p+r
                                prs = word[-pr]
                                if prs not in roottree: break
#                                elif not freqnotrank: # ranking
#                                    if postfixes[postfix]==0 or roottree[prs][0]<postfixes[postfix]:
#                                        postfixes[postfix]=roottree[prs][0]
#                                        if is_good_ending(postfix):
#                                            if endings[postfix]==0 or roottree[prs][0]<endings[postfix]:
#                                                endings[postfix]+=roottree[prs][0]
#                                elif roottree[prs][0]>0 and r==1 and is_good_root(word[-p-rootlen:-p],word): # frequence
#                                    postfixes[postfix]+=roottree[prs][0]
#                                    if is_good_ending(postfix):
#                                        endings[postfix]+=roottree[prs][0]
                                root=word[-p-rootlen:-p]
                                if r==1 and roottree[prs][0]>0 and is_good_root(root,word): # frequence
                                    postfixes[postfix]+=rawprevocab[root]
                                    if is_good_ending(postfix):
                                        endings[postfix]+=rawprevocab[root]
                                roottree = roottree[prs][1]
                posttree = posttree[ps][1]
        minsufflen = 1
        # extract suffixes
        for postfix in postfixes:
            for pos in range(minsufflen,len(postfix)-1):
                suffix=postfix[:pos]
                ending=postfix[pos:]
                if endings[ending]>0:
                    suffixes[suffix]+=postfixes[postfix]
        # regularize weight
        for postfix in postfixes:
            if len(postfix)<longenoughpplen: # longer ppfixes are better
                expo = longenoughpplen - len(postfix)
                postfixes[postfix] = postfixes[postfix] // round(ppregbase**expo)
        for suffix in suffixes:
            if len(suffix)<longenoughpplen: # longer ppfixes are better
                expo = longenoughpplen - len(suffix)
                suffixes[suffix] = suffixes[suffix] // round(ppregbase**expo)
        # print to files
        if postfile is not None:
            for item in sorted(postfixes.items(),key=lambda x: x[1],reverse=True):
                postfile.write(" {0} {1}\n".format(item[0],item[1]))
        if sufffile is not None:
            for item in sorted(suffixes.items(),key=lambda x: x[1],reverse=True):
                sufffile.write(" {0} {1}\n".format(item[0],item[1]))
        if endfile is not None:
            for item in sorted(endings.items(),key=lambda x: x[1],reverse=True):
                endfile.write(" {0} {1}\n".format(item[0],item[1]))
    return postfixes,suffixes,endings

def explore_codetree_plus(codetree,tword,wordpos0=0,emptysubword=False):
    store={}
    if emptysubword:
        store[0]=0 # for empty subword
    wlen = len(tword)
    for wordpos in range(wordpos0,wlen):
        s = tword[wordpos]
        if s not in codetree:
            break
        val = codetree[s][0]    
        if val>0:
            pos = wordpos-wordpos0+1
            store[pos]=val
        codetree = codetree[s][1]
    return store

def extend_subword_matrix(dest,src,addempty=False,dstartpos=0):
    for dpos in range(len(dest)):
        if dpos>=dstartpos:
            ddict=deepcopy(dest[dpos])
            for ditem in ddict.items():
                dlen=ditem[0]
                drank=ditem[1]
                spos = dlen+dpos
                if spos<len(src):
                    for sitem in src[spos].items():
                        slen=sitem[0]
                        srank=sitem[1]
                        rank=max(drank,srank)
                        dslen=dlen+slen
                        if dslen not in dest[dpos]:
                            dest[dpos][dslen]=rank
                        elif rank<dest[dpos][dslen]:
                            dest[dpos][dslen]=rank
        if addempty:
            dest[dpos][0]=0

def merge_subword_matrix(dest,src,addempty=False,dstartpos=0):
    for dpos in range(len(dest)):
        if dpos>=dstartpos:
            for sitem in src[dpos].items():
                slen=sitem[0]
                srank=sitem[1]
                if slen not in dest[dpos]:
                    dest[dpos][slen]=srank
                elif srank<dest[dpos][slen]:
                    dest[dpos][slen]=srank
        if addempty:
            dest[dpos][0]=0

def reverse_subword_matrix(mx,emptysubword=True):
    mlen = len(mx)
    if emptysubword:
        rmx = [{0:0} for i in range(mlen)]
    else:
        rmx = [{} for i in range(mlen)]
    for pos in range(mlen):
        seq = mx[pos]
        for seqel in seq.items():
            sublen=seqel[0]
            subrate=seqel[1]
            lastpos = pos+sublen-1
            pos2 = mlen-lastpos-1
            rmx[pos2][sublen]=subrate
#            rmx[pos2].append((sublen,subrate))
    return rmx

def build_codetree_best(ppvocab,rate,reverse,datafile=None,loadfile=False):
    """ Collect best prefixes (reverse=False) or postfixes (reverse=True)
    """
    if loadfile:
        codetree = read_codetree(datafile,reverse)
    else:
        codetree = {}
        icount = len(ppvocab.items())
        if rate>1.0: bestcount=int(rate)
        else: bestcount = int(round(icount * rate))
        prevfreq = 0
        numx = 0
        num = 0
        for item in sorted(ppvocab.items(),key=lambda x: x[1],reverse=True):
            if numx>=bestcount: break
            freq = int(item[1])
            if freq!=prevfreq: num+=1
            word = item[0]
            numout = num    
            if datafile is not None:
                datafile.write(u" {0} {1}\n".format(word,numout))
            if reverse: word=word[::-1]
            add_to_codetree_terminal(word,codetree,numout)
            prevfreq = freq
            numx += 1
    return codetree

def extract_root(precodetree,bestprecodetree,bestpostcodetree,word,minrootlen,bestcount):
    # create candidate list of prefixes, with a prefix denoted as its length
    prestore = explore_codetree_plus(bestprecodetree,word,0,True)
    # create candidate list of postfixes, with a postfix denoted as its length
    poststore = explore_codetree_plus(bestpostcodetree,word[::-1],0,True)
    roots = Counter()
    wlen = len(word)
    for xpos in prestore.items(): # all available prefixes
        pos = xpos[0]
        for ypos in poststore.items(): # all available postfixes
            pos2rev = ypos[0]
            if pos+pos2rev+minrootlen<=wlen:
                pos2 = wlen-pos2rev
                root=word[pos:pos2]
#                postfix = word[pos2:]
                if (search_codetree(root,precodetree)>0
                    and is_good_root(root,word)
                    and search_codetree(root,badroots)==0
                    ):
                    prerank=xpos[1]
#                    if pos>0:
#                        if verbose:
#                            print("{1}({0})".format(prerank,word[:pos]),end=" ")
                    rootrank = search_codetree(root,precodetree)
#                    if verbose:
#                        print("{1}[{0}]".format(rootrank,root),end=" ")
                    postrank=ypos[1]
#                    if pos2rev>0:
#                        if verbose:
#                            print("{1}({0})".format(postrank,postfix),end=" ")
#                    if freqnotrank:
#                        rootrate = rootrank-prerank-postrank
#                    else:
                    rootrate = prerank+rootrank+postrank
#                    rootrate = rootrank #+prerank+postrank
                    roots[root]=rootrate
#                    if verbose:
#                        print("+{0}".format(rootrate))
    minroots=[]
    if len(roots)>0:
        cnt=0
        for root in sorted(roots,key=lambda x: roots[x]):
#            if root=="eirop":
#                print("rootx",roots[root])
            minroots.append(root)
            cnt+=1
            if cnt>=bestcount: break
#        minroot=min(roots,key=lambda x: roots[x])
    return minroots #,roots[minroot]
    
longenoughrootlen = 5
rootregbase = 4
minrootfreq = 2

def collect_roots(vocab,rawprecodetree,bestprecodetree,bestpostcodetree,datafile=None,loadfile=False,bestcount=1):
    if loadfile:
        roottree = read_codetree(datafile)
    else:
        roottree = {}
        roots = Counter()
        for root in goodroots:
            roots[root] = goodroots[root]
        for word in vocab:
            minroots = extract_root(rawprecodetree,bestprecodetree,bestpostcodetree,word,minrootlen,bestcount)
            cnt=0
            for root in minroots:
                freq = search_codetree(word,rawprecodetree)
                if freq>0:
                    roots[root] += vocab[word]
                cnt+=1
        for root in roots:
            if len(root)<longenoughrootlen: # longer roots are better
                expo = longenoughrootlen - len(root)
                roots[root] = roots[root] // round(rootregbase**expo)
        prevfreq = 0
        numx = 0
        num = 0
        for root in sorted(roots,key=lambda x: roots[x], reverse=True):
            freq = roots[root]
            if freq<minrootfreq: break
            if freq!=prevfreq: num+=1
            if datafile:
                datafile.write(u" {0} {1}\n".format(root,num))
            add_to_codetree_terminal(root,roottree,num)
            numx += 1
            prevfreq = freq
#        print("roots",numx)
    return roottree
                
rootfactor = 1
rootblockweight = 1000000

# status: 0-prefix, 1-root, 2-postfix, 3-endings
def segment_word0(mxx,word,pos,step,status,track,trackweight,trackstore,trackweightstore):
    if pos>=len(mxx[status]): return # finished after prefix
#    print(pos,step,status,len(track))
#    print("SPV",status,pos,mxx[status][pos])
    wordlen=len(word)
    for candidate in mxx[status][pos].items():
        pos2 = pos + candidate[0]
        if status==1: # root
            trackweight2 = trackweight + candidate[1] * rootfactor
        else:
            trackweight2 = trackweight + candidate[1]
        if step==len(track):
            track.append([pos2,candidate[1]])
        else:
            track[step] = [pos2,candidate[1]]
        if status<=1: # prefix or root
            segment_word0(mxx,word,pos2,step+1,(status+1)%3,track,trackweight2,trackstore,trackweightstore)
        else: # post
            if pos2==wordlen:
                tracktostore = list(track[:step+1])
                trackstore.append(tracktostore)
                trackweightstore.append(trackweight2+len(tracktostore)*rootblockweight//3)
#                print("added",tracktostore)
            else:
                segment_word0(mxx,word,pos2,step+1,(status+1)%3,track,trackweight2,trackstore,trackweightstore)

maxgerootlen = 9
nent_placeholder_marker = "@###"
maxnenums = 1

def obtain_segment_track(bestprecodetree,roottree,
                         bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,word,
                         generateroots=True,extramode=0,verbose=False):
    """ Collect list of segmentation tracks, each in form (prefix, root, postfix)+ and compute weights (the less, the better)
        and return the best one
    """
    if extramode!=1 and extramode!=4 and word in bestvocab or len (word)>20:
        return None # None indicates word from bestvocab later (in segment_word)
    
    prematrix = []
    for pos in range(len(word)):
        prematrix.append(
                explore_codetree_plus(bestprecodetree,word,pos)
                )
    pre2 = deepcopy(prematrix)
    extend_subword_matrix(prematrix,pre2,True)
    if verbose:
        sys.stdout.write("PRE\n")
        for pos in range(len(prematrix)):
            sys.stdout.write("{0} {1} {2}\n".format(pos,word[pos],prematrix[pos]))
#            print(pos,word[pos],prematrix[pos])

    rootmatrix = []

    for pos in range(len(word)):
        rootmatrix.append(
                explore_codetree_plus(roottree,word,pos)
                )

    if verbose:
        sys.stdout.write("ROOT\n")
        for pos in range(len(rootmatrix)):
            sys.stdout.write("{0} {1} {2}\n".format(pos,word[pos],rootmatrix[pos]))

    endmatrix0 = []
    postmatrix0 = []
    suffmatrix0 = []
    for pos in range(len(word)):
        endmatrix0.append(
                explore_codetree_plus(bestendcodetree,word[::-1],pos)
                )
        suffmatrix0.append(
                explore_codetree_plus(bestsuffcodetree,word[::-1],pos)
                )
    if verbose:
        sys.stdout.write("POST00\n")
        for pos in range(len(postmatrix0)):
            sys.stdout.write("{0} {1} {2}\n".format(pos,word[::-1][pos],postmatrix0[pos]))
        sys.stdout.write("SUFF00\n")
        for pos in range(len(suffmatrix0)):
            sys.stdout.write("{0} {1} {2}\n".format(pos,word[::-1][pos],suffmatrix0[pos]))

    if extramode == 1 or extramode == 2 or extramode == 3 or extramode == 4:
        lastxend0 = deepcopy(endmatrix0[0])
#        print('lastxend',lastxend,word)
#    if extramode == 1 or extramode == 2 or extramode == 3 or extramode == 4:
#        extend_subword_matrix(endmatrix0,suffmatrix0,False,1)
#        merge_subword_matrix(endmatrix0,suffmatrix0,False,1)
#    else:
#        extend_subword_matrix(endmatrix0,suffmatrix0,False)
#        merge_subword_matrix(endmatrix0,suffmatrix0,False)
    extend_subword_matrix(endmatrix0,suffmatrix0,False)
    merge_subword_matrix(endmatrix0,suffmatrix0,False)
    postmatrix0 = endmatrix0
#    print("POSTM",postmatrix0)

    if verbose:
        sys.stdout.write("POST0\n")
        for pos in range(len(postmatrix0)):
            sys.stdout.write("{0} {1} {2}\n".format(pos,word[::-1][pos],postmatrix0[pos]))
    postmatrix = reverse_subword_matrix(postmatrix0,True)
    postmatrix.append({0:0})
    if verbose:
        sys.stdout.write("POST\n")
        for pos in range(len(postmatrix)):
            wordplus=word+" "
            sys.stdout.write("{0} {1} {2}\n".format(pos,wordplus[pos],postmatrix[pos]))
            
    track = [[0,0] for i in range(len(word)*2)]
    trackweight = 0
    trackstore = []
    trackweightstore = []

#    if extramode != 2:
    mxx = [prematrix,rootmatrix,postmatrix]
    segment_word0(mxx,word,pos=0,step=0,status=0,track=track,
                  trackweight=trackweight,trackstore=trackstore,trackweightstore=trackweightstore)
    
        # extramode=1: named-entity processing in training phase - stem except for best words
        # extramode=2: named-entity processing in translation phase - stem
        # extramode=3: named-entity processing in translation phase - placeholders
        # extramode=4: named-entity processing in training phase - inserting placeholders (except for best words)
    if extramode == 1 or extramode == 2 or extramode == 3 or extramode == 4:
        lastx = postmatrix0[0]
        lastxend = {}
        if len(lastxend0) > 0:
            for ee in lastxend0:
#                print(ee,word[-ee:],is_good_ending_ne(word[-ee:]))
                if is_good_ending_ne(word[-ee:]):
                    lastxend[ee] = lastxend0[ee]
#        print("LASTX",lastx,extramode)
#        print('tracktore',trackstore)
#        print('trackweightstore',trackweightstore,word)
        if len(lastx)>0:
            bestlist = sorted(lastx.keys(),key=lambda x: lastx[x])
            for i in range(len(bestlist)):
                best=bestlist[i]
                bestweight=lastx[best]
                if len(word[:-best])>=minrootlen and is_good_root(word[:-best],word):
                    track=[[0,0],[len(word)-best,bestweight],[len(word),0]]
                    trackstore.append(track)
                    trackweightstore.append(bestweight)
                    break
#        print('len(trackweightstore)',len(trackweightstore))
        if extramode == 1 or extramode == 2: # stem
            if len(trackweightstore)==0 or len(lastxend)==0:
#                print('nostore',word)
                besttrack2 = [[(i+2)//3,0] for i in range(len(word)*3)]
            else:
#                print("lastxend",lastxend,word)
                besttrack = trackstore[argmin(trackweightstore)]
                rootendpos = besttrack[1][0]
                besttrack2 = [[(i+2)//3,0] for i in range(rootendpos*3)]
        elif extramode == 3 or extramode == 4: # ending
            phlen = len(nent_placeholder_marker)
            if maxnenums == 1: phlenplus = phlen
            else: phlenplus = phlen + 1
            if len(trackweightstore)==0 or len(lastxend)==0:
                besttrack2 = [[0,0],[phlen,0],[phlen,0],[phlen,0],[phlenplus,0],[phlenplus,0]]
            else:
                besttrack = trackstore[argmin(trackweightstore)]
                rootendpos = besttrack[1][0]
                postfixlen = len(word)-rootendpos
                if postfixlen==0:
                    besttrack2 = [[0,0],[phlen,0],[phlen,0],[phlen,0],[phlenplus,0],[phlenplus,0]]
                else:
                    besttrack2 = [[0,0],[phlen,0],[phlen,0],[phlen,0],[phlenplus,0],[phlenplus,0],
                                  [phlenplus,0],[phlenplus+postfixlen,0],[phlenplus+postfixlen,0]]
    #            print("##Besttrack3",word,besttrack2)
        return besttrack2
    # unable to find track from available roots
    elif len(trackweightstore)==0:
        if generateroots:
            for pos in range(len(word)):
                for candidatelen in range(2,min(maxgerootlen,len(word)-pos)+1):
                    candidateroot=word[pos:pos+candidatelen]
                    if is_good_root(candidateroot,word):
                        rootrank = search_codetree(candidateroot,roottree)
                        if rootrank>0:
                            rootmatrix[pos][candidatelen]=rootrank
                        else:
                            # x*candidatelen...: more letters generated roots make rank worse
                            # candidatelen+1: more generated roots make rank worse
                            # (one generated root of length 2n is better than two of lengths 4 each)
                            rootmatrix[pos][candidatelen]=rootblockweight*(candidatelen+1)
            if verbose:
                sys.stdout.write("ROOT2\n")
                for pos in range(len(rootmatrix)):
                    sys.stdout.write("{0} {1} {2}\n".format(pos,word[pos],rootmatrix[pos]))
            segment_word0(mxx,word,pos=0,step=0,status=0,track=track,
                          trackweight=trackweight,trackstore=trackstore,trackweightstore=trackweightstore)
        else: # do not generate roots, take only postfix
            lastx = postmatrix0[0]
            if len(lastx)>0:
                bestlist = sorted(lastx.keys(),key=lambda x: lastx[x])
                for i in range(len(bestlist)):
                    best=bestlist[i]
                    bestweight=lastx[best]
                    if len(word[:-best])>=minrootlen and is_good_root(word[:-best],word):
                        track=[[0,0],[len(word)-best,bestweight],[len(word),0]]
                        trackstore.append(track)
                        trackweightstore.append(bestweight)
                        break
    if verbose:
        num=0
        for t in trackstore:
            sys.stdout.write("{0} {1} {2}\n".format(num,trackweightstore[num],t))
            num+=1
        sys.stdout.write("{0}\n".format(trackweightstore))

    if len(trackweightstore)==0: return []
    else:
        if verbose:
            sys.stdout.write("{0}\n".format(argmin(trackweightstore)))
            sys.stdout.write("{0}\n".format(trackstore[argmin(trackweightstore)]))
        return trackstore[argmin(trackweightstore)]

def mark_alpha_segmentation(roottree,bestvocab,track,word,marker1,mode,optmode=1):
    """ Generate segmented word given track
    """
    if len(track)==0: # no track built
        if mode==3:
            segmentlist=[word+marker1]
        else:
            segmentlist=[word]
    else:
        wordpos=0
        segmentlist = []
        status = 0 # 0-prefix, 1-root, 2-postfix
        t = 0
        while t < len(track):
#            trackpos = track[t]
            wordposx = track[t][0]
            if status==0: # PRP optimization
                wordposy = track[t+1][0]
                wordposz = track[t+2][0]
                if optmode==0:
                    pass
                elif optmode==1:
                    segmenty = word[wordpos:wordposy] # prefix+root
                    segmentxyz = word[wordpos:wordposz] # p+r+p
                    segmentyz = word[wordposx:wordposz] # r+p
                    if segmentxyz in bestvocab and word[wordpos:wordposx] not in nonprefixes_dict:
                        # concatenate prefix+root+postfix, reduces amount of segments
                        if t+3<len(track) or mode>0:
                            track[t][0]=wordpos
                            track[t+1][0]=wordposz
                            track[t+2][0]=wordposz
                    elif wordposz>wordposy and segmentyz in bestvocab:
                        # concatenate root+postfix, reduces amount of segments
                        if t+3<len(track) or mode>0:
                            track[t+1][0]=wordposz
                    elif wordposx>wordpos and search_codetree(segmenty,roottree)>0: # prefix+root is among roots
                        track[t][0]=wordpos
#                        track[t+1][0]=wordposy # prefix added to root
                    elif track[t+1][1]>rootblockweight and t+3<len(track):
                        # generated roots (not in last position) concatenated
                        # with its prefix and postfix, reduces amount of segments
                        if word[wordpos:wordposx] not in nonprefixes_dict:
                            track[t][0]=wordpos
                        track[t+1][0]=wordposz
#                        track[t+2][0]=wordposz
                elif optmode==2:
                    if t+3<len(track):
                        # roots (NOT in last prp position) concatenated
                        # with its prefix and postfix, reduces amount of segments
                        if word[wordpos:wordposx] not in nonprefixes_dict:
                            track[t][0]=wordpos
                        track[t+1][0]=wordposz
#                        track[t+2][0]=wordposz
                    else:
                        # roots (in last prp position) concatenated
                        # with its prefix (not postfix), reduces amount of segments
#                        wordposz = track[t+2][0]
                        if word[wordpos:wordposx] not in nonprefixes_dict:
                            track[t][0]=wordpos
#                        track[t+1][0]=wordposy
#                        track[t+2][0]=wordposz
            wordpos2 = track[t][0]
            if wordpos2>wordpos:
                segment = word[wordpos:wordpos2]
                if mode==0:
                    segmentlist.append(segment)
                elif mode==1:
                    if status==0: #prefix marked
                        segmentlist.append(segment+marker1)
                    elif status==1:
                        segmentlist.append(segment)
                        wordpos3 = track[t+1][0]
                        isprelast = (t==len(track)-2)
                        # if the root is not the last root and no postfix follows
                        if not isprelast and wordpos3-wordpos2==0:
                            segmentlist.append(marker1)
                    elif status==2:
                        segmentlist.append(marker1+segment)
                        islast = (t==len(track)-1)
                        if not islast:
                            segmentlist.append(marker1)
                elif mode==2:
                    if status==0: #prefix marked
                        segmentlist.append(segment+marker1)
                    elif status==1:
                        segmentlist.append(segment)
                    elif status==2:
                        segmentlist.append(marker1+segment)
                elif mode==3:
                    segmentlist.append(segment+marker1)
                            
            wordpos = wordpos2
            status = (status+1)%3
            t+=1
    return segmentlist

def create_nent_placeholder(nenum):
    if maxnenums == 1:
        return nent_placeholder_marker
    else:
        return nent_placeholder_marker + str(nenum)

def segment_word(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                 word,marker1,marker2,mode,generateroots=False,optmode=1,extramode=0,nenum=0,verbose=False):
    """ Preprocess string before segmentation into list of alpha(letters) and non-alpha parts,
        alpha parts are then prp segmented, and then segmented word put together with segmentation marks,
        considering also uppercase/lowercase processing
        mode=0: marker1 denotes end of word
        mode=1: marker1 denotes prefix/postfix and link
        mode=2: marker1 denotes prefix/postfix and begin/end
        mode=3: marker1 denotes link to next segment (like in BPE)
        mode+100: no uppercase processing (marker2 denotes uppercase for the first letter of the following segment)
        optmode: optimization mode used in 'mark_alpha_segmentation'
        extramode=0: no named-entity processing
        extramode=1: named-entity processing in training phase - stem except for best words
        extramode=2: named-entity processing in translation phase - stem
        extramode=3: named-entity processing in translation phase - placeholders
        extramode=4: named-entity processing in training phase - inserting placeholders (except for best words)
    """
    segmentlist = []
    pos0 = 0
    alpha = False
    prevalpha = False
    endsbyroot = False
    AlphaProcessed = True
    uppercasemode = mode<100
    mode %= 100
    tracknone=False
    if extramode!=1 and extramode!=4 and word in bestvocab:
        segmentlist.append(word)
    else:
#        if extramode==4:
#            word = "abc."
        for pos in range(len(word)+1): # symbol by symbol processing; takes one position after end to process last segment
            if pos<len(word):
                alpha = word[pos].isalpha()
            if pos==len(word) or pos > 0 and alpha != prevalpha: # boundary of alpha/nonalpha parts
                subword=word[pos0:pos] # original case
                subwordplus=subword # case optionally set to lower
                if prevalpha: # process alpha part
                    if pos0>0: # if alpha part follows non-alpha part, the non-alpha part marked
                        if mode==0: segmentlist[-1] += marker1
                        elif mode==1: segmentlist.append(marker1)
                    AlphaProcessed = False
                    if isUlower2(subword):
                        subwordplus = subwordplus[0].lower() + subwordplus[1:]
                        if uppercasemode:
                            segmentlist.append(marker2)
                            subword = subwordplus
                    track = obtain_segment_track(bestprecodetree,roottree,
                            bestsuffcodetree,bestpostcodetree,bestendcodetree,
                            bestvocab,subwordplus,generateroots,extramode,verbose)
                    if track is None:
                        track = []
                        tracknone = True
                    if verbose:
                        sys.stdout.write("TRACK {0}\n".format(track))
                    if mode==0:
                        if len(track)==0: endsbyroot=False
                        elif track[-1][0]==track[-2][0]: # empty postfixpart
                             # only root of length <=3 (thus considered to be small word without marker as separate segment)
                            # (empty prefix and root length <=5) 
                            if len(track)==3 and track[-3][0]==0 and track[-2][0]-track[-3][0]<=5:
                                endsbyroot=False
                            else:
                                endsbyroot=True
                        else: endsbyroot=False
                    if extramode==3 or extramode==4:
                        if len(track)<=6:
                            subword = create_nent_placeholder(nenum)
                        else: #if len(track)==9:
                            postlen = track[-2][0] - track[-5][0]
                            subword = create_nent_placeholder(nenum) + subword[-postlen:]
                    elif extramode==2 or extramode==1:
                        pass
                    segmentlist+=mark_alpha_segmentation(roottree,bestvocab,track,subword,marker1,mode,optmode)
                    islast = (pos==len(word))
                    if islast and mode==0:
                        if endsbyroot: # marker set after word as separate segment
                            segmentlist += marker1
                            AlphaProcessed = True
                        else:
                            segmentlist[-1] = marker1 + segmentlist[-1] # postfix or small word marked (marker before it as part of it)
                            AlphaProcessed = True
    
                else: # process non alpha part -- no segmentation performed -- forwarded to BPE
                    if not AlphaProcessed:
                        AlphaProcessed = True
                        if mode==0: subword = marker1 + subword
                        elif mode==1: segmentlist.append(marker1)
                    if mode==3: subword += marker1
                    segmentlist.append(subword)
                    endsbyroot = False
                pos0 = pos
            prevalpha = alpha
    if mode==2: # postprocessing with begin/end
        len1=len(marker1)
        if len(segmentlist)==1: # single segment: do nothing
            pass
        elif len(segmentlist)==2 and segmentlist[0]==marker2: # single segment preceeded by uppercase mark: do nothing
            pass
        elif len(segmentlist)==2 and segmentlist[-1][:len1]==marker1: # two segments ended by postfix
            segmentlist[-1] = marker1 + segmentlist[-1]
        # the same with uppercase mark
        elif len(segmentlist)==3 and segmentlist[0]==marker2 and segmentlist[-1][:len1]==marker1:
            segmentlist[-1] = marker1 + segmentlist[-1]
        else: # to put begin and end marks
            # BEGINNING
            # if uppercase mark or prefix in the beginning: add marker to it
            if segmentlist[0]==marker2 or segmentlist[0][-len1:]==marker1:
                segmentlist[0]+=marker1
            else: # otherwise add extra marker
                segmentlist.insert(0,marker1)
            # END
            # if postfix in the end: add marker to it
            if segmentlist[-1][:len1]==marker1:
                segmentlist[-1] = marker1 + segmentlist[-1]
            else: # otherwise add extra marker
                segmentlist.append(marker1+marker1)
    elif mode==3:
        len1=len(marker1)
        if segmentlist[-1][-len1:]==marker1:
            segmentlist[-1] = segmentlist[-1][:-len1]
    return segmentlist,tracknone
    
def segment_sentence_preprocess_ne(sentence,verbose=False):
    # EXTRACT named entities simple
    wnum = 0
    nentnums = []
    for word in sentence.split():
        if isUlower2(word):
#            print(word)
            nentnums.append(wnum)
        wnum += 1
#    print(nentnums)
    nentnumsplus = []
    prev = -9
    i = 0
    count = 0
    for num in nentnums:
        if num-prev>1:
            count = 1
        else:
            count +=1
        nentnumsplus.append(count)
        prev = num
        i += 1
    i = len(nentnumsplus)-1
    while i>=0:
        if nentnumsplus[i]<=2: i-=1
        else:
            for k in range(nentnumsplus[i]):
                nentnumsplus[i]=0
                i-=1
    nentnums2 = []
    for i in range(len(nentnums)):
        if nentnumsplus[i]>0:
            nentnums2.append(nentnums[i])
    return nentnums2
    
#nent_marker = "@$$$"
#
#def create_nent_line(word):
#    return nent_marker + " " + word + "."

def segment_sentence(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                     sentence,marker1,marker2,mode=0,generateroots=False,optmode=1,extramode=0,nentnums=[],nentsegs=[],verbose=False):
    """ Segment line of words (whitespace-tokenized string) with PRP encoding
    """
    output = []
    i = 0
    nnum = 0
    for word in sentence.split():
        if i in nentnums:
            segmented = nentsegs[nnum]
            nnum = (nnum + 1) % 10
        else:
            segmented,tracklen = segment_word(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                                     word,marker1,marker2,mode,generateroots,optmode,extramode,0,verbose)
        if mode%100==2: # optimizing usage of begin/end markers (omitting end marker, if begin marker follows)
            if len(output)>0 and output[-1]==marker1+marker1: # previous word ended by separate endmarker
                if segmented[0]==marker1: # current word starts by marker
                    del output[-1]
                if segmented[0][-len(marker1)*2:]==marker1+marker1: # current word starts by prefix marked as beginning
                    del output[-1]
        output += segmented
        i += 1
    return ' '.join(output)

def segment_sentence_nents(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                     sentence,marker1,marker2,mode=0,generateroots=False,optmode=1,extramode=2,nentnums=[],nentsegs=[],verbose=False):
    """ Extract named-entities from sentence and prepare them for output
    """
    output = []
    nentnumspost = []
    i = 0
    nnum = 0
    for word in sentence.split():
        if i>0 and i in nentnums:
            sword,tracknone = segment_word(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                                     word+'.',marker1,marker2,mode,generateroots,optmode,extramode,0,verbose)
            if tracknone==False:
                if mode%100==2: # optimizing usage of begin/end markers (omitting end marker, if begin marker follows)
                    if len(output)>0 and output[-1]==marker1+marker1: # previous word ended by separate endmarker
                        if sword[0]==marker1: # current word starts by marker
                            del output[-1]
                        if sword[0][-len(marker1)*2:]==marker1+marker1: # current word starts by prefix marked as beginning
                            del output[-1]
                word2 = word + '.'
                word3 = segment_sentence(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,
                                           bestvocab,word2,marker1=marker1,marker2=marker2,mode=mode,
                                           generateroots=generateroots,optmode=optmode,extramode=extramode)
                output.append(word3)
                nentnumspost.append(i)
                nnum += 1
                if nnum==10: break
        i += 1
    return output,nentnumspost

def segment_sentence_ne_placeholder(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                     sentence,marker1,marker2,mode=0,generateroots=False,optmode=1,extramode=0,nentnums=[],nentsegs=[0],verbose=False):
    """ segment line of words (whitespace-tokenized string) with PRP encoding
    """
    output = []
    nentnumspost = []
    i = 0
    nnum = nentsegs[0]
    for word in sentence.split():
        if i>0 and i in nentnums:
            sword,tracknone = segment_word(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                                     word+".",marker1,marker2,mode,generateroots,optmode,extramode,nnum,verbose)
            if tracknone==False:
                if mode%100==2: # optimizing usage of begin/end markers (omitting end marker, if begin marker follows)
                    if len(output)>0 and output[-1]==marker1+marker1: # previous word ended by separate endmarker
                        if sword[0]==marker1: # current word starts by marker
                            del output[-1]
                        if sword[0][-len(marker1)*2:]==marker1+marker1: # current word starts by prefix marked as beginning
                            del output[-1]
                output.append(sword)
                nentnumspost.append(i)
                nnum = (nnum+1)%10
        i += 1
    nentsegs[0]=nnum
    return output

# code 9474: '│'; code 9553: '║'
def apply_prpe(infile,outfile,infilepref,infileroot,infilesuff,infilepost,infileend,infilebestvocab,marker1="9474",marker2="9553",bigmode=1,generateroots=False,lang='lv'):
    """segment input stream with PRP encoding
    """
    if marker1.isdigit(): marker1 = chr(int(marker1))
    if marker2.isdigit(): marker2 = chr(int(marker2))

    add_heuristics(lang)
    
    mode = bigmode % 1000
    optmode = bigmode // 1000 % 10
#    optmode = optmode0 % 10
#    extramode = optmode0 // 10

    bestprecodetree = read_codetree(infilepref,reverse=False)
    bestsuffcodetree = read_codetree(infilesuff,reverse=True)
    bestpostcodetree = read_codetree(infilepost,reverse=True)
    bestendcodetree = read_codetree(infileend,reverse=True)
    roottree = read_codetree(infileroot)
    bestvocab = read_vocabulary(infilebestvocab,reverse=False)
    for sentence in infile:
        outfile.write(segment_sentence(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                    sentence,marker1=marker1,marker2=marker2,mode=mode,generateroots=generateroots,
                    optmode=optmode,extramode=0).strip())
        outfile.write(' \n')

# code 9474: '│'; code 9553: '║'
def apply_prpe_ne_train(infile,outfile,infilepref,infileroot,infilesuff,infilepost,infileend,infilebestvocab,
                        infilenent,marker1="9474",marker2="9553",bigmode=1,generateroots=False,lang='lv'):
    """segment input stream with PRP encoding with named-entity proessing for training phase
    """
    if marker1.isdigit(): marker1 = chr(int(marker1))
    if marker2.isdigit(): marker2 = chr(int(marker2))

    add_heuristics(lang)
    
    mode = bigmode % 1000
    optmode = bigmode // 1000 % 10

    bestprecodetree = read_codetree(infilepref,reverse=False)
    bestsuffcodetree = read_codetree(infilesuff,reverse=True)
    bestpostcodetree = read_codetree(infilepost,reverse=True)
    bestendcodetree = read_codetree(infileend,reverse=True)
    roottree = read_codetree(infileroot)
    bestvocab = read_vocabulary(infilebestvocab,reverse=False)
    nent = read_nent(infilenent)
    lnum = 0
    if outfile is None:
        lnum = 22
#    lnum2 = 0
    phnum = 0
    nnums = [0]
    for sentence in infile:
        lnum+=1
        nentnumspost = []
        nentsegspost = []
        if lnum in nent:
            nentnums = segment_sentence_preprocess_ne(sentence)

            segmented_ne,nentnumspost = segment_sentence_nents(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                                         sentence,marker1,marker2,mode,generateroots,optmode=optmode,extramode=1,
                                         nentnums=nentnums,nentsegs=[])
            segmented_ne = segmented_ne[:1]
            nentnumspost = nentnumspost[:1]
            if outfile is None:
                print('#segmented_ne',segmented_ne,nentnumspost)
            if len(segmented_ne)>0:
                for ne in segmented_ne:
                    if outfile is not None:
                        outfile.write(ne)
                        outfile.write(' \n')
                    else:
                        print('#ne',ne)
                nentsegspost = segment_sentence_ne_placeholder(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                                 sentence,marker1,marker2,mode,generateroots,optmode=optmode,extramode=4,
                                 nentnums=nentnumspost,nentsegs=nnums)
            phnum = (phnum+1)%10
        sgm = segment_sentence(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                    sentence,marker1=marker1,marker2=marker2,mode=mode,generateroots=generateroots,optmode=optmode,
                    extramode=0,nentnums=nentnumspost,nentsegs=nentsegspost).strip()
        if outfile is not None:
            outfile.write(sgm)
            outfile.write(' \n')
        else:
            print("#apply_train",sgm)

# code 9474: '│'; code 9553: '║'
def apply_prpe_ne_translate(infile,outfile,infilepref,infileroot,infilesuff,infilepost,infileend,infilebestvocab,
                            outfilenent,marker1="9474",marker2="9553",bigmode=1,generateroots=False,lang='lv'):
    """segment input stream with PRP encoding with named-entity proessing for translation phase
    """
    if marker1.isdigit(): marker1 = chr(int(marker1))
    if marker2.isdigit(): marker2 = chr(int(marker2))

    add_heuristics(lang)
    
    mode = bigmode % 1000
    optmode = bigmode // 1000 % 10

    bestprecodetree = read_codetree(infilepref,reverse=False)
    bestsuffcodetree = read_codetree(infilesuff,reverse=True)
    bestpostcodetree = read_codetree(infilepost,reverse=True)
    bestendcodetree = read_codetree(infileend,reverse=True)
    roottree = read_codetree(infileroot)
    bestvocab = read_vocabulary(infilebestvocab,reverse=False)
    lnum = 1
    for sentence in infile:
        nentnums = segment_sentence_preprocess_ne(sentence)[:1]
        nentnumspost = []
        nentsegspost = []
        if len(nentnums)>0:
            segmented_ne,nentnumspost = segment_sentence_nents(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                                         sentence,marker1,marker2,mode,generateroots,optmode=optmode,extramode=2,nentnums=nentnums,nentsegs=[])
            segmented_ne = segmented_ne[:maxnenums]
            nentnumspost = nentnumspost[:maxnenums]
            if len(segmented_ne)>0:
                for ne in segmented_ne:
                    if outfile is not None:
                        outfile.write(ne)
                        outfile.write(' \n')
                    else:
                        print(ne)
                if outfilenent is not None:
                    outfilenent.write('{0} {1}\n'.format(lnum,len(segmented_ne)))
                nentsegspost = segment_sentence_ne_placeholder(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                                 sentence,marker1,marker2,mode,generateroots,optmode=optmode,extramode=3,
                                 nentnums=nentnumspost,nentsegs=[0])

        sgm = segment_sentence(bestprecodetree,roottree,bestsuffcodetree,bestpostcodetree,bestendcodetree,bestvocab,
                    sentence,marker1=marker1,marker2=marker2,mode=mode,generateroots=generateroots,optmode=optmode,
                    extramode=0,nentnums=nentnumspost,nentsegs=nentsegspost).strip()
        if outfile is not None:
            outfile.write(sgm)
            outfile.write(' \n')
        else:
            print("apply_translate",sgm)
        lnum += 1

def learn_prpe(infile,outfilepref,outfileroot,outfilesuff,outfilepost,outfileend,outfilebestvocab,ratepref=20,ratesuff=400,ratepost=0.1,ratevocab=10000,
              ingoodpref=None,inbadpref=None,ingoodroot=None,inbadroot=None,ingoodpost=None,inbadpost=None,iterations=1,lang='lv'):
    """learn PRP encoding - raw prefixes, prefixes, roots, suffixes, postfixes, endings
    """
    global goodprefixes
    global badprefixes
    global goodroots
    global badroots
    global goodpostfixes
    global badpostfixes
    if ingoodpref is not None: goodprefixes = read_vocabulary(ingoodpref)
    if inbadpref is not None: badprefixes = read_codetree(inbadpref)
    if ingoodroot is not None: goodroots = read_vocabulary(ingoodroot)
    if inbadroot is not None: badroots = read_codetree(inbadroot)
    if ingoodpost is not None: goodpostfixes = read_vocabulary(ingoodpost)
    if inbadpost is not None: badpostfixes = read_codetree(inbadpost)
    
    bestprecodetree = None
    roottree = None
    bestpostcodetree = None

    add_heuristics(lang)

    rawprecodetree,rawpostcodetree,vocab,rawprevocab=register_subwords(infile,premaxlen,postmaxlen,minrootlen)

    # PRP extraction
    mainprefrate = 0.05
    mainpostrate = 0.05

    suffrate = ratesuff
    lastpostrate = ratepost
    lastprefrate = ratepref
    iters = iterations
    save_vocabulary(outfilebestvocab,vocab,order=True,reverseorder=True,alphaonly=False,
                    maxcount=ratevocab)
#    save_vocabulary(outfilebestvocab,vocab,True,True,True,ratevocab)
    for it in range(iters):
        # first processing
        if it==0: # first
            prefsource = rawprecodetree
            rootsource = rawprecodetree
            postsource = rawpostcodetree
        else: # not first
            prefsource = bestprecodetree
            rootsource = roottree
            postsource = bestpostcodetree


#                postrate = mainpostrate
        if it<iters-1: # not last
            prefout = None
            postout = None
            suffout= None
            endout = None
            prefrate = mainprefrate**(1/(iters-it))
            postrate = mainpostrate**(1/(iters-it))
            bestprefout = None
            bestsuffout = None
            bestendout = None
            bestpostout = None
            rootout = None
        else: # last
            prefout = None
            postout = None
            suffout= None
            endout = None
            prefrate = lastprefrate
            postrate = lastpostrate
            bestprefout = outfilepref
            rootout = outfileroot
            bestsuffout = outfilesuff
            bestendout = outfileend
            bestpostout = outfilepost
        
        # second processing
        prevocab = analyze_prefixes(prefsource,rootsource,vocab,rawprevocab,prefout,loadfile=False)
        postvocab,suffvocab,endvocab = analyze_postfixes(rootsource,postsource,vocab,rawprevocab,postout,suffout,endout,loadfile=False)
        
        bestprecodetree = build_codetree_best(prevocab,rate=prefrate,reverse=False,datafile=bestprefout,loadfile=False)
        bestpostcodetree = build_codetree_best(postvocab,rate=postrate,reverse=True,datafile=bestpostout,loadfile=False)
        roottree=collect_roots(vocab,rawprecodetree,bestprecodetree,bestpostcodetree,rootout,loadfile=False,bestcount=1)

    build_codetree_best(suffvocab,rate=suffrate,reverse=True,datafile=bestsuffout,loadfile=False)
    build_codetree_best(endvocab,rate=1.0,reverse=True,datafile=bestendout,loadfile=False)

def unprocess_line_prpe(sentence,marker1,marker2,mode):
    output = []
    len1 = len(marker1)
    len2 = len(marker2)
    upper = False
    marked = False
    markednext = False
    wordstarted = False
    mode %= 100
    for word in sentence.split():
        # uppercase marking
        if word==marker2:
            upper=True
            continue
        elif mode==2 and word[:len2]==marker2: # in mode=2
            upper=True
            word = word[len2:]
        elif upper:
            word = word[0].upper() + word[1:]
            upper = False
        if mode==0:
            # determine connection to previous segment
            if word==marker1:
                marked = False
                continue
            elif word[:len1]==marker1 and not word[len1].isalpha():
                word = word[len1:]
                marked = True
            elif word[:len1]==marker1:
                word = word[len1:]
                markednext = False
            elif word.isalpha():
                markednext = True
            if word[-len1:]==marker1 and not word[len1].isalpha():
                word = word[:-len1]
                markednext = True
            # add segment
            if marked:
                output[-1]+=word
                marked = False
            else:
                output.append(word)
            # determine connection to next segment
            if markednext:
                markednext = False
                marked = True
        elif mode==1:
            # determine connection to previous segment
            if word==marker1:
                marked = True
                continue
            elif word[:len1]==marker1:
                marked = True
                word = word[len1:]
            # add segment
            if marked:
                output[-1]+=word
                marked = False
            else:
                output.append(word)
            # determine connection to next segment
            if output[-1][-len1:]==marker1:
                marked = True
                output[-1] = output[-1][:-len1]
        elif mode==2:
            if word==marker1: # beginning as separate marker
                wordstarted = True
                output.append('')
            elif word==marker1+marker1: # end as separate marker
                wordstarted = False
            elif word[-len1*2:]==marker1+marker1: # beginning as prefix
                wordstarted = True
                output.append(word[:-len1*2])
            elif word[:len1*2]==marker1+marker1: # end as postfix
                wordstarted = False
                output[-1]+=word[len1*2:]
            else:
                if word[-len1:]==marker1: # prefix
                    word = word[:-len1]
                elif word[:len1]==marker1: # postfix
                    word = word[len1:]
                if wordstarted:
                    output[-1]+=word
                else:
                    output.append(word)
        elif mode==3:
            if marked:
                output[-1]+=word
            else:
                output.append(word)
            marked = False
            if output[-1][-len1:]==marker1:
                output[-1]=output[-1][:-len1]
                marked = True
            
    return ' '.join(output)

# code 9474: '│'; code 9553: '║'
def unprocess_prpe(infile,outfile,marker1="9474",marker2="9553",mode=1):
    if marker1.isdigit(): marker1 = chr(int(marker1))
    if marker2.isdigit(): marker2 = chr(int(marker2))
    for line in infile:
        outfile.write(unprocess_line_prpe(line,marker1,marker2,mode).strip())
        outfile.write(' \n')

def unprocess_prpe_ne_train(infile,outfile,infilenent,marker1="9474",marker2="9553",mode=1):
    if marker1.isdigit(): marker1 = chr(int(marker1))
    if marker2.isdigit(): marker2 = chr(int(marker2))
    nnum = 0
    lnum = 1
    linesleft = -1
    nentlist = []
    lnents = read_nent(infilenent)
    for line in infile:
        pline = unprocess_line_prpe(line,marker1,marker2,mode).strip()
#        lft1 = pline[:len(nent_marker)]
        if lnum in lnents and linesleft == -1: # nent line
            nent = pline.strip('.')
            if outfile is None:
                print("NENT",nent)
            nent = nent[0].upper()+nent[1:]
            nentlist.append(nent)
            linesleft = 0
        else: # regular line
            plist = []
            for p in pline.split():
                if p[:len(nent_placeholder_marker)]==nent_placeholder_marker:
#                    print("!!!",p)
                    p = p[:len(p)-1]
                plist.append(p)
            pline = " ".join(plist)
            if outfile is None:
                print(pline)
            for nent in nentlist:
                pline = pline.replace(create_nent_placeholder(nnum),nent)
                nnum = (nnum+1)%10
            if outfile is None:
                print(nentlist)
                print(pline)
            else:
                outfile.write(pline)
                outfile.write(' \n')
            nentlist = []
            linesleft = -1
            lnum += 1

def unprocess_prpe_ne_translate(infile,outfile,infilenent,marker1="9474",marker2="9553",mode=1):
    if marker1.isdigit(): marker1 = chr(int(marker1))
    if marker2.isdigit(): marker2 = chr(int(marker2))
    lnum = 1
    linesleft = -1
    nentlist = []
    lnents = read_nent_int(infilenent)
    for line in infile:
        pline = unprocess_line_prpe(line,marker1,marker2,mode).strip()
#        lft1 = pline[:len(nent_marker)]
        if lnum in lnents and linesleft == -1: # first nent line
            linesleft = lnents[lnum]
        if linesleft > 0: # nent line
#            nent = pline[len(nent_marker)+1:].strip('.')
            nent = pline.strip('.')
            if outfile is None:
                print("NENT",nent)
            nent = nent[0].upper()+nent[1:]
            nentlist.append(nent)
            linesleft -= 1
        else: # regular line
            plist = []
            for p in pline.split():
                if p[:len(nent_placeholder_marker)]==nent_placeholder_marker:
#                    print("!!!",p)
                    p = p[:len(p)-1]
                plist.append(p)
            pline = " ".join(plist)
            if outfile is None:
                print(pline)
            nnum = 0
            for nent in nentlist:
                pline = pline.replace(create_nent_placeholder(nnum),nent)
                nnum = (nnum+1)%10
            if outfile is None:
                print(nentlist)
                print(pline)
            else:
                outfile.write(pline)
                outfile.write(' \n')
            nentlist = []
            linesleft = -1
            lnum += 1
            