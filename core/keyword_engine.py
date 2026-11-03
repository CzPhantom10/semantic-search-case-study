"""BM25 retrieval over the same indexed chunks used by semantic retrieval."""
import re, math
from collections import Counter

def tokenize(text): return re.findall(r"[\w]+(?:['’-][\w]+)*",text.lower(),flags=re.UNICODE)

class KeywordEngine:
    def __init__(self, chunks, k1=1.5, b=.75):
        self.chunks=chunks; self.k1=k1; self.b=b
        self.tokens=[tokenize(c['text']) for c in chunks]
        self.lengths=[len(t) for t in self.tokens]; self.avg=sum(self.lengths)/len(self.lengths) if self.lengths else 0
        self.df=Counter(w for ts in self.tokens for w in set(ts))
    def search(self, query, k=5):
        q=tokenize(query)
        if not q or not self.chunks:return []
        scores=[]; n=len(self.chunks)
        for i,terms in enumerate(self.tokens):
            tf=Counter(terms); score=0
            for term in q:
                f=tf[term]
                if f:
                    idf=math.log(1+(n-self.df[term]+.5)/(self.df[term]+.5))
                    norm=f+self.k1*(1-self.b+self.b*self.lengths[i]/(self.avg or 1))
                    score+=idf*f*(self.k1+1)/norm
            if score>0:scores.append((score,i))
        scores.sort(reverse=True)
        return [{'chunk_id':self.chunks[i]['chunk_id'],'text':self.chunks[i]['text'],'score':score,'metadata':self.chunks[i]} for score,i in scores[:k]]
