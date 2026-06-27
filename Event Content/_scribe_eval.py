import os, re, json, subprocess, glob, collections

BASE="/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/Event Content"
ENV="/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/.env"
key=None
for line in open(ENV):
    if line.startswith("ELEVENLABS_API_KEY="): key=line.strip().split("=",1)[1]
assert key and key.startswith("sk_"), "no key"

events=["05 21 26","06 03 26","06 04 26"]
AUD=(".m4a",".mp3",".wav",".mp4",".aac")

def find_files(folder):
    audio=None;abest=-1;cands=[]
    for f in os.listdir(folder):
        p=os.path.join(folder,f); low=f.lower()
        if not os.path.isfile(p): continue
        if low.endswith(AUD) and os.path.getsize(p)>abest: abest=os.path.getsize(p); audio=p
        if low.endswith((".md",".txt")) and not any(x in low for x in ("slide","brief","post-event","scribe","readme")):
            cands.append(p)
    transcript=max(cands,key=os.path.getsize) if cands else None
    return audio,transcript

def keyterms(text,cap=80):
    seqs=re.findall(r'\b([A-Z][a-zA-Z0-9.&+-]+(?:\s+[A-Z][a-zA-Z0-9.&+-]+){0,4})\b',text)
    acr=re.findall(r'\b([A-Z]{2,6})\b',text)
    cnt=collections.Counter()
    for s in seqs:
        s=s.strip()
        if 2<=len(s)<=49 and len(s.split())<=5: cnt[s]+=1
    for a in acr:
        if 2<=len(a)<=49: cnt[a]+=1
    stop=set("The This That And But So We You It In On Of To For With My Our If As Is Are What How When Why Yeah Okay Right Like Thank Thanks Hi Hey Hello Just I'm It's Yes No Now Here There".split())
    out=[]
    for t,c in cnt.most_common():
        if t in stop: continue
        if " " in t or c>=2: out.append(t)
        if len(out)>=cap: break
    return out

def transcribe(audio,kt,outjson):
    args=["curl","-sS","-X","POST","https://api.elevenlabs.io/v1/speech-to-text",
          "-H","xi-api-key: "+key,"-F","file=@"+audio,
          "-F","model_id=scribe_v2","-F","diarize=true","-F","timestamps_granularity=word",
          "-F","language_code=eng","-F","num_speakers=6","-o",outjson,"-w","%{http_code}"]
    for t in kt: args+=["-F","keyterms="+t]
    return subprocess.run(args,capture_output=True,text=True).stdout.strip()

def readable(jp,outmd,title):
    d=json.load(open(jp)); words=d.get("words",[])
    end=max((w.get("end") or 0) for w in words) if words else 0
    sp=sorted({w.get("speaker_id") for w in words if w.get("speaker_id")})
    lines=[];cur=[None];buf=[]
    def flush():
        if buf: lines.append("**["+str(cur[0])+"]** "+("".join(buf)).strip()); buf.clear()
    for w in words:
        if w.get("type","word")=="word" and w.get("speaker_id") and w["speaker_id"]!=cur[0]:
            flush(); cur[0]=w["speaker_id"]
        buf.append(w.get("text",""))
    flush()
    md="# %s — ElevenLabs Scribe v2 transcript\n\n_scribe_v2 · diarized · keyterms · ~%d min · %d tokens · %d speakers_\n\n"%(title,end/60,len(words),len(sp))
    open(outmd,"w").write(md+"\n\n".join(lines))
    return end/60,len(words),len(sp),d.get("text","")

for ev in events:
    fs=[f for f in glob.glob(os.path.join(BASE,ev+"*")) if os.path.isdir(f)]
    if not fs: print("\n###",ev,"NO FOLDER"); continue
    folder=fs[0]; name=os.path.basename(folder)
    audio,transcript=find_files(folder)
    print("\n### "+name)
    print(" audio:",os.path.basename(audio) if audio else None,"| transcript:",os.path.basename(transcript) if transcript else None)
    if not audio: print(" SKIP (no audio)"); continue
    ttext=open(transcript,encoding="utf-8",errors="ignore").read() if transcript else ""
    kt=keyterms(ttext)
    print(" keyterms:",len(kt),"|",", ".join(kt[:10]))
    outjson=os.path.join(folder,"eleven_scribe_v2.json")
    code=transcribe(audio,kt,outjson)
    if code!="200":
        print(" HTTP",code,"ERROR:",open(outjson).read()[:200] if os.path.exists(outjson) else "?"); continue
    mins,toks,spk,etext=readable(outjson,os.path.join(folder,name+" — Transcript (Scribe v2).md"),name)
    exwords=len(ttext.split())
    print(" ElevenLabs: %.0f min | %d tokens | %d speakers || existing transcript: %d words"%(mins,toks,spk,exwords))
    multi=[t for t in kt if " " in t][:14]
    ex=ttext.lower(); el=etext.lower()
    print(" %-26s %6s %7s"%("key entity (from existing)","exist","eleven"))
    for t in multi: print("   %-25s %6d %7d"%(t[:25],ex.count(t.lower()),el.count(t.lower())))
    print(" --- existing sample ---\n  ",ttext[:380].replace("\n"," "))
    print(" --- eleven sample ---\n  ",etext[:380].replace("\n"," "))
print("\nDONE")
