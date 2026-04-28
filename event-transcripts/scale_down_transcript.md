Great to meet you. All my name is Neil Patel. I'm the co-founder and CEO of scale down, which will be learning a lot about today. What we do is we build task specific small language models for your agents, specifically your voice agents for the folks in the room today.  
5  
Speaker 5  
25:41  
And being a free trial  
1  
Speaker 1  
25:43  
PSC is for offering 50 million tokens to any accounts and agents assignment for free.  
7  
Speaker 7  
25:50  
I'll tell you why you can use that. That's how you can use it. Um, so I know a lot of you folks are building the PlayStations, but really, today, voice agents are just text getting transcribed into voice. So, really, in the back end of the text that you're working on is really what's important, and so I'll show you kind of just like a text version of what we built our flagship product is a compression, small language model.  
26:13  
So, basically, what that does, is, it cleans up all the mo easy contacts that you're about to throw into your lll.  
8  
Speaker 8  
26:20  
So that your lab is cheaper, faster, and more happier. I'll show you how that works too. A simple, messy example. Don't move it on the screen. Yeah.  
26:34  
Cool. Um, so for those of you that are soccer fans, you know that Messi is the go? Um, and kind of what we were originally dealing with when we started building rag chat box. It was too much context was going into the the large size. So, we set out to solve that problem with the skill.  
26:56  
So, you see, here kind of the original problem, which includes the system prompt that Nano engineers write the contacts to which, in this case, is the Wikipedia article about Messi and the question that a user wants, right? So you see the full Wikipedia article here, which is a common way that context is time adjusted.  
7  
Speaker 7  
27:15  
And so what we do is scale. Now is we don't touch your system wrong. Ever or your user query, but we use that to do context compression  
8  
Speaker 8  
27:23  
on the actual input from Wikipedia that you'd be pulling into your house and so what you see here is the compress confidence. And this is the benefits that you get so effectively. You lower the number of tokens  
5  
Speaker 5  
27:37  
by 60 plus percent, so instead of ingesting a thousand tokens to get to this original response. You're now only adjusting around 300 350\.  
9  
Speaker 9  
27:46  
Uh, that means that if you were doing this a million times, that instead of paying five and a half Grand, you would not be paying less than 2K. Um, most importantly, for voice folks in the room, you know, latency kills, and so this cuts down the latency of that all alcohol in  
5  
Speaker 5  
28:00  
half because you're adjusting way fewer, so that means that your users can do double the fruit bite at the same time per second, so that's a simple example, right? A couple like a thousand tokens? When you actually see all this up and you think about? Real workloads with a lot of context.  
28:19  
We work with a lot of finance companies, for example,  
8  
Speaker 8  
28:22  
so they're putting in times of context years, right? So, I'll give you a real example, and we can crank up the compression mark. You can choose what the freshman you want, and then you'll kind of see what this is.  
1  
Speaker 1  
28:36  
Well, that works. I'll pause for any immediate questions anyways.  
5  
Speaker 5  
28:40  
Yeah, yeah, well. So, how big is that one? Yeah, um, so that one is a full 10K, so some more customer we call, like financial reports, to get to those answers. And so it's around.  
29:00  
Yeah, so you can see here in the in the output, right?  
29:13  
Uh, yeah, yeah, so whenever contacts you're throwing in. So, like, if let's say you have rat, right? Yeah, throwing in the chunks that you've already pulled from your Vector database. That, like re-ranking, is just moving things around and kind of choosing the right order for them. What we're doing is actually going into each individual chunk using the user query and the system prompts instruction set to determine what tokens are actually relevant to put into the larger file down here so?  
2  
Speaker 2  
29:41  
So, this was, like, the pre-processing layer before your health.  
5  
Speaker 5  
29:47  
So, we built these models to basically sit in front of the other one. To make the ll1 work marketing way, so it doesn't have to adjust a bunch of noise, and you have to pay for all the memories.  
2  
Speaker 2  
30:05  
Yeah, yeah. So,  
5  
Speaker 5  
30:07  
yeah, that's exactly what you could use this for so you can throw this five thousand. Uh, like, 10 days went to our API, and it would depressed out. But the key thing here is that it's at runtime, so it would be when you're doing your inference when your user is abuses.  
7  
Speaker 7  
30:23  
If you want to have like a wall by example, conversation, and you know your, your first prompt is about one part one piece of the context, and the second problem is about a different reason that I'm, like, yeah, is it able to retrieve it as well, like, how does that work?  
30:36  
Yeah, so  
5  
Speaker 5  
30:37  
that's actually a very common use case that we get, um, caption, right, like Cloud code does that per code? Um, some of our users are like deep research AI companies, so you have like a bunch of unstructured data that they're pulling into deep research off the web?  
2  
Speaker 2  
30:53  
In here. And  
5  
Speaker 5  
30:54  
then you'll ask one particular question, and then, as  
7  
Speaker 7  
30:56  
humans that we can do a lot of different questions, and they'll go in a different direction,  
2  
Speaker 2  
31:00  
so you basically  
7  
Speaker 7  
31:00  
use the latest query to compile, like, basically query aware of compressions. And it, doesn't it affect?  
8  
Speaker 8  
31:10  
Swan Stein if you're compressing every time the new prompt is coming up. Yeah, so  
2  
Speaker 2  
31:15  
I'll show you in a kind of Laura voice demo, but like, like you can see here, latency is reduced, because if you're producing the number of debits right instead of your llm like 5.4, processing 128, 000 buildings. It's now processed from 2002.00 information, so your latency actually defines by two nearly.  
31:33  
Maybe it runs the compression on each interaction, making each question yeah? Is it possible?  
6  
Speaker 6  
31:40  
Yeah, yeah, or somewhere like 200 milliseconds. That's why we built this whole 90 miles for this particular task. Okay, because they are  
2  
Speaker 2  
31:46  
very close.  
6  
Speaker 6  
31:47  
That's what we like our number one seller is accuracy, so we make sure that accuracy stays consistent, but very close second is late, right? Okay.  
2  
Speaker 2  
31:57  
The money say that actively, so I might be able to recall as an exact sentence from like the original document, for example. Like, if you asked it to. Yeah, citations are a common use case, so we don't change. Like, if you take a com between, so, this context right here versus the context up here.  
32:16  
You can easily click into our product to see what actually got removed, uh. But the the key idea here is is extractive supervis. Or compression, so it's not abstractive. It doesn't change any of the words it purely cuts out, the things that are irrelevant, and you can tune that to, like what we determine as relative orders.  
32:36  
Yeah,  
6  
Speaker 6  
32:37  
yeah, so that was kind of like in line with my like. Can  
2  
Speaker 2  
32:41  
you  
9  
Speaker 9  
32:41  
modify the context after you, uh, we get like more significant response from you?  
2  
Speaker 2  
32:48  
Yeah, so we do so. Basically, our model is out of the box are very good, like up to 30 to 40 is where you compression rate or where you see no change in accuracy across the board across a lot of different use cases. A lot of the folks want to get to like 60, 70, 80 percent compression rates, and that's where we can work with them to fine-tune and train the specific out of the box model that we have for their particular use case with their data, and so we have that Services.  
8  
Speaker 8  
33:15  
Is the small language model that was actually using the compression  
2  
Speaker 2  
33:18  
here. Yeah,  
9  
Speaker 9  
33:19  
okay? And are you guys using, like OCR, or like, it's proprietary, like, um,  
2  
Speaker 2  
33:24  
so OCR is like pulling information from like the the PDFs and things like that. Yeah, so we don't have OCR built in for this, and all the no image purely natural language X, uh, but what we've done basically is build these small and smallest front scrap for particular news.  
33:39  
So, what you're seeing here is our compression, um, small language model, which we built originally from the garage. But we now have kind of built out other smaller models that aren't just like pre-processing layers for large language models. They're actually slms themselves, so you're using like Haiku, or 5.4 or something like that.  
33:58  
But summarization or classification, we actually have models that are built specifically for those costs of summarizing data extraction and possibilities. And oh, Truck Smashers and Paul Stranger particular tasks, because our thought process is that task surface.  
5  
Speaker 5  
34:15  
What like the outcome of using small models are especially if like sub agents or large high volume agentic workflows and you can train them to any particular appreciate if you want. Or, like, the general purpose models today, kind of suck at a lot of definitely the process that we're doing with that.  
2  
Speaker 2  
34:33  
Cool, um, so no questions on the tech side. Uh, Hermes had challenged me to ask of using the Bora, uh, agent studio. And so, my team and I built an example of this, and you can see. With an actual Agora system in place. So, a new podcast from Sequoia dropped today.  
34:54  
I didn't want to listen to the whole thing because I had s\*\*\* to do, and so. Um, I put it in here.  
35:04  
What should you guys be able to hear this myself?  
35:11  
Hello, how can I help you today? We're the two speakers in this podcast.  
35:36  
Okay, so. All right, we'll give her another three.  
35:45  
Hello, how can I help you today? Who are the two speakers in this podcast?  
35:56  
The two featured speakers at songs.  
4  
Speaker 4  
35:59  
Anton from mobile. The host also says he interviewed two friends of mine Monty from 11 lab and Anton from lovable. What was the community Anton started in soccer?  
36:16  
He said he started a community called Stockholm AI.  
2  
Speaker 2  
36:22  
When did Maddie meet his co-founder?  
36:34  
Great. Um, so those are just some examples of questions that you can ask. But the key thing here, yeah, this is really, um.  
8  
Speaker 8  
36:45  
Um, so kind of similar to the previous demo you can see here, kind of on the top left. It's the number of tokens that we compressed. So before, if you have drawn this just monogoro without scale down, uh, 13, 000 tokens, we can press that nearly in half to 7, 000 tokens of the actual podcast transcript that's gone into your agent.  
37:05  
But most importantly, for all of you boys, parents in the room latency went down by 25, 30, right before. Over 2000 milliseconds would scale down. It was 14, and that includes our agency that we have for our production Center for your questions. So, net late T savings about 500 milliseconds and then in the top right.  
37:28  
This is just accuracy to see, like between the Baseline response and scaled down response. How similar were there, um? And for those of you that know about llm as a judge, eval is about 90\. It's pretty good, um, so that's where you can see in the top right here, and you can obviously read the bass process to see.  
37:46  
That's effectively what you have to scale on is compressed inputs into your large language models. Your voice, so you got faster and cheaper and better results? Let's go there. Pretty pleasure.  
4  
Speaker 4  
38:05  
Um, so num zero. I'm actually talking that to you quite a bit, um? So how to think about Montero is that?  
7  
Speaker 7  
38:12  
Like, you said, I'm not sure we definitely points, right? And so, they basically are the layer that actually allows them to know, like for us to know how you are asking for different products, and I'm asking for a different product that when you pull up the Agora website, the second time they know what to pitch you versus the thing with you, and they have a a contest history about it.  
2  
Speaker 2  
38:31  
Yeah,  
7  
Speaker 7  
38:32  
I thought we had your complexions. Yeah, so they have a compassion Futures for historical context, like the actual memory that you have ours is more of a real time run time. Know. What about getting alcoholics? It's rather than a storage memory that.  
38:49  
And the other question. Yeah, I mean from.  
9  
Speaker 9  
38:55  
People reaching out to you guys in companies using Auntie guys. Where are you seeing, like the most traction or the both  
2  
Speaker 2  
39:00  
the  
9  
Speaker 9  
39:00  
types of companies, but also maybe some of the use cases where people seem to be leaning into this, at least to start. Yeah. I think high volume workflows with a lot of context is obviously where the pressure gets. Full models make no sense.  
2  
Speaker 2  
39:13  
So a lot of Finance, use cases, legal use cases. And then, like the surprising one that we've been seeing a lot of in, like, been bound from, is like the social listening deep research world where, um, companies that are doing like cyber security or scraping like credit anything in Twitter and stuff.  
39:29  
Those photos are putting a lot of like petabytes of data into analons every day. Um, so our workers are those places as well, uh, we mostly again believe in working on, like, uh, the like, rag, and like text based world, uh. But Hermes and those folks have kind of made me.  
8  
Speaker 8  
39:46  
Realize that voice really needs something like this, especially for like document-based voice agents and customer support and things like. Not so, we're kind of dumping down. That's true.  
2  
Speaker 2  
40:01  
Yeah, so we have two options, uh, you can either hit our API. We're supposed on AWS. We have all the security self-dual information up.  
5  
Speaker 5  
40:10  
So you can do that for developers, but for larger Enterprises and customers, we do containerize our model that can find another popular VPC and stuff. They just set up the typing with.  
1  
Speaker 1  
40:22  
Put it in front of the, um, like the cloud request  
2  
Speaker 2  
40:26  
early. Yeah, yeah. So, with  
8  
Speaker 8  
40:28  
some of the Enterprises that, we kind of like, given them our model to run. They've set that up, um, in their own, where they need to but generally not to before their own models that they trained in house. Otherwise, you. Potential customers that way. How they. How would they like to see their use case?  
40:49  
Yeah, so I mean, that's where the 50 million free tokens for everyone comes from. So Dr, behind a UPI.  
7  
Speaker 7  
40:56  
It's containerizing. Our model doesn't much more expensive gas, so that's generally reserved for Enterprises. And that's often times when they want containerized version of our models. They want to fine-tune them, so that becomes become much more where. Work like a project with them. But yeah, we offer UPS for both payrolls outfit with each other.  
41:16  
That's it.  
8  
Speaker 8  
41:17  
Yeah, give me an example. I just showed you going back to the Dora slide with the architecture as you only be replacing, like the new LM pieces on that chart, or are you replacing my face speaking  
2  
Speaker 2  
41:33  
from Texas 100 or something as well,  
8  
Speaker 8  
41:34  
not discussion Texas, so I was honestly. We're not even on that grass media editor used to be in maybe in that custom llm. Do you see we need to workplace that you'd like within that? Yeah, so the same way you would?  
1  
Speaker 1  
41:47  
Like your rag in there or whatever else you need to do. You would make your call out to rag and not to scale down and then that response you  
8  
Speaker 8  
41:54  
feedback. Let's say you're using like a Gemini LM or something that work, but like it wouldn't replace that or it. Would it just works alongside that? Yeah, yeah. So it's a pre-processing layer for that Gemini call. Because, like if you weren't to use scale now, right? That should be these.  
42:12  
These numbers are like you would be sending Gemini 13 000 tokens for these three questions. Is, if you set scale that up. Before that, Gemini call that Gemini model will only get. 7, 000 of the relevant evidence, and so keep out here. See the same, the three latency, Etc, so it's like a pre-processing there before that Gemini call, uh, but that's the context compression one.  
42:34  
So, just to clarify context and correction goes involvement that we recommended to sit in front of an hour alarm. Yeah, versus we have other models like I was looking to earlier that are smalling models that were placed like haiku, gbt 5.4 mini, and Etc. So if you're doing like high volume workloads where the task is very straightforward.  
42:53  
Somewhere else. This document or classify this, like? Customer support query or whatever those types of high volume workflows. We built models from scratch that specifically do classification at the same quality as a Frontier model light 5.4 or Opus 4.7, but are 10 to 100 times cheaper and are more accurate doing that particular time, because all the big models are General purposes.  
43:19  
You do anything and everything our models we built for specific costs. So, if your agent is basically doing something very straightforward and said, what a lot of times that that? Replace that, driving my model with the scale, not a model. But the most simple way to do it is just Pat.  
43:33  
That's how long it is that we built for complex compression in front temperature? Does that make sense? Yeah, yeah, cool. I've got one more questions, but I'll chat tonight. Yeah, hey, do  
7  
Speaker 7  
43:44  
you play these any for Benchmarks, uh, on hallucination of blankets? Uh, yeah, of course. Uh, so their website is. Okay, so these are some of our benchmarks. Uh, so we've released.  
8  
Speaker 8  
44:06  
Uh, basketball three, and I'm working on our body. But the tldr is that we were state of the art for finance fetch, which is a common like Finance workflow, and so basically what we did was this compression model. Was we sat it in front of 5.4? And that increased the accuracy of 5.47 while reducing the number of tokens by seven years.  
44:27  
Because now 5.4 doesn't have to adjust 700 000 tokens. We can ingest literally, like 5, 000 token, and it has much higher quality and accuracy before. There's Neo and a stop type Aquariums. So, that's our big one for depression, which is why all the clients companies are coming to us.  
44:46  
But summarization is another common ones have, like all the like. Granolas bottoms, like all the meat and note takers, there's a popular restaurant called Q and some. And our model was comparable, if not better, than iPhone sort of a large model. Is there? On the right side, and as he comes, and then classification, the common use cases model route it.  
45:11  
So, if we work with open router. They're great friends of ours, but like a lot of companies are trying to not use open router all the time, uh, until they're building their own routers internally, and our classification models are really a good use case for that. So we do it Benchmark again.  
45:23  
So, most of the model router companies, um, and so you can classify queries that are coming in and drive it to the rack model using our classification model, and that was, uh, nine used to the P went with.  
1  
Speaker 1  
45:37  
Thank you\! Yeah, you're welcome.  
8  
Speaker 8  
45:41  
And yeah, um, I apologize in advance. If this sounds a little mean, but what? Why is this better than if I'm engineer just saying, hey, I'll just run it through some small model myself, even if I don't get as high quality viewers of our your flight tier models are.  
46:00  
It's really just an extra step that I can learn myself. Yeah, um, so that's how we started. We used off the shelf, open source models, uh, Liberta models like changed up the architecture a little bit, uh, dropped accuracy at 20, 25, because they weren't actually built for understanding the relevance of things.  
46:19  
So you can do that for sure. If your customers can just stop using your product because it'll be worse,  
2  
Speaker 2  
46:25  
um, so I think the general idea is that like?  
8  
Speaker 8  
46:28  
Small models as a pre-processing layer is a great plan. I highly recommend doing that for all of you folks out there. Because oftentimes you're feeding. Oh, I'm just trying to talk because it aren't really necessary. So, for efficiency, highly recommend using an SLM, I think. Just do the evals to test what the actual output quality does.  
46:46  
If you do that.  
46:54  
You have any cartridge Apartments? Follow. We have any models specifically for graduates or something. No, no. What do you envisioning?  
2  
Speaker 2  
47:04  
Yeah, we are. We are like testing out some, like eval models, okay, um? But yeah.  
8  
Speaker 8  
47:17  
Well, I'll be up here. If you guys want to shop, thanks for everyone. I just want to take one picture because.  
1  
Speaker 1  
47:32  
Thank you\! Thank you.  
8  
Speaker 8  
48:12  
I'm good\! Are you guys?  
2  
Speaker 2  
48:28  
Hi Anton\!  
1  
Speaker 1  
48:51  
And soup. So, I mean, we're we're pretty into those with, like, uh, so. And before, that works. Yeah, so there's always more crucial and I do, and uh, yeah.  
2  
Speaker 2  
49:34  
All right, ready?  
Transcribed by Pixel  
00:08  
\-49:38  
   
 

