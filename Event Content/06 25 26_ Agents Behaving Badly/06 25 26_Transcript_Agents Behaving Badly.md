Speaker 1   00:00  
I'm also an LP and a small fund called generationship. If you want to ask me about that later, please do. I held startups, uh, go to market with clinical Services, so that describes you. Please talk to me afterwards, um. So, thanks to their dog for hosting, this is a lovely space.

This is my favorite place to go for for meetups. I think you all agree with that, um, and.

Speaker 2   00:24  
Datadog, I think, uh, has a startup program where, if you are series a, and before you can qualify for a hundred thousand dollars worth of credits in the first year, so talk to there's some literature back there on the table, and you can also talk to Arielle, uh, and she'll be happy to directing the right way, so we have a lovely panel for you today, um.

And then, who gets my mic? All right, so take it away.

Speaker 1   00:52  
Thank you. Hi everyone. Thanks for joining me. Um, there's one get a raise of hand to get to see who's in the audience is. Here is an engineer. Anyone? A new product?

Speaker 3   01:07  
Nice and miscellaneous. Nice\! I'm miscellaneous, um, so my name is Angela Chief of staff at artiflex. We help with zero generate generation and evaluation, uh, then. I'll be hosting this panel, so I'll let our catalyst Julian, Michael, and Joe introduce themselves, and then we'll get into the questions. Um, I think the panel will take 30 minutes.

We'll have a few questions at at prepared, and then we'll poke it up. Okay? Hi, um. First of all, it's really great. Should be here. Fantastic. Fantastic to be here. Such a great. Um, thanks for data talk for hosting this and talking with us for being here for our effects for organizing us.

So, my background, I actually have a very weird background. I have a physics PhD, you know, I guess I, I said, like data analysis there. Uh, then I came to Princess a postdoc with some AI for physics and moved to language models, and I was working on Sui bench.

I don't know who was familiar with sweet bench before.

Um, and and sweet H. And like, so those have both kind of software engineering benchmarks and Asian. Um, and it's like a couple of months. I'm basically doing exact same thing, and

Speaker 4   02:27  
I want to promote your program. Man, uh, as

Speaker 3   02:31  
Well, sometimes promote our most recent benchmark called program bench, which is very challenging. Now, I gotta do that Benchmark. Um, yeah, so my name is Michael. I'm a software engineer here. I work on our Asian observability products.

Speaker 5   02:47  
I've been here for seven months before that I was at Meadow for 20 years. So, yeah, so? As I said, yeah, so, uh, yeah. That's basically that. I mean, I only grow up so.

Speaker 6   02:59  
Hi, everyone\! I'm angel at the co-founder of our place. I'm also a professor at Columbia CS, so my area of expertise is actually processing. So nowadays, it's all large language models, um, particularly. Archlex is working on uter simulations, has a way for automated testing of patients and evaluation of agents, of course, is the data core of potential URL training to solve.

So, we must be working on how can you assimilate in terms and close to your real user behavior? And this is intrinsically writing optimization problem that requires data and machine learning better operations. Thank you for making this.

Speaker 3   03:41  
So, first question is when you hear an evaluation, what does that actually mean in the context of ancient systems?

Speaker 2   03:51  
I don't know which audible.

Speaker 3   03:54  
On,

Speaker 2   03:55  
Okay, um. So, for me, the the big difference between Asian evaluation and normal, I think it's give a prompt, and you get like a response back. It's really that you're looking. I said end-to-end tasks like I must still gets offer engineering tasks, and they're like the classical task is like, I give you a bag, and then the agent can explore Pokemon your file system.

You know, make random edits, you know, destroy your good history. I don't know what it does. Hopefully Tesla changes, and then submit garbage or not. You know, uh, and evil means, then to test whether it's submit garbage or not, but it's like a very kind of, like, a longer process in many steps.

Yeah, so I guess it'll be nice, um?

Speaker 4   04:40  
I usually

Speaker 7   04:41  
Certainly Bell to be everything you're doing to make sure your agent is

Speaker 4   04:44  
Behaving in fraud. Um, actually, the products get a really good blog posts on this where they have this, like swish Keys model that they borrowed from the security space, and they sort of. Consider everything from like people that are red, teaming their Foundation models, you know, down into, like almost unit level evals to do eval.

Um, so, so for me, I mean, kind of, maybe the um? Uh, you know, just a few examples of things would be on. The smallest scale would be something that is looking at your agent and verifying that it is selecting the right tools, right, like when, for instance, if you have a chat bot that, um, you know, it's meant to help you with Airline reservations, and you ask a question about your existing reservation.

Well, it's not going to give you the right answer unless it selects the tool that knows how to look up your reservation so you can eval that. And that's kind of like the smallest level. On the largest level would be things like red team or agent right. Having humans go and do it.

You know, be back a little bit from that. You could take

Speaker 7   05:39  
What that team is doing to what you know. The red teamers are doing turn them into. How long as a judge put them in online, evalis, significant through, and sort of everything from their down? So it's all eval, and that's a lot of fun, because then, uh, when you have any conversation about eval, you're almost certainly talking about a different thing than the other person's functional.

So, then first say we would, but what do you might know?

Speaker 6   06:02  
Yeah,

Speaker 4   06:03  
Um, I think, like, they're traditionally looking for talking about validations and mission learning. You always have a static bench where I'm going. This is the question. This is the answer, and this is a brown truth. Whenever we have a model that generators, we compare it within round through the syring.

It says what we usually account reference phase in violation, but in reality when agents come those sort of most powerful and magical thing is, we don't preset, like, what's the next step for the agent you give in all the hardness, like the tools that you give it and? To try to do multi-step and then come up to the outcome.

Original, like the final goals, so you can't say like you, you have to do this tool at this moment, so evaluation more is looking on interaction. And then, most importantly, in like, how do you define what is considered to be completion or a task success? So, for each individual scenarios where you shouldn't even know task.

It has to be defined as highly different because it's all

Speaker 6   07:00  
About digit user. For example, um, in a ranking, was a customer service engine. Did the user get the things that they wanted to do in the first place for a doctor so that that is the sort of the past success, but that's only a one measure. Different friend.

And the original

Speaker 3   07:46  
Company

Speaker 6   07:46  
Policies domain knowledge policies as well. So, I think like an evaluation right now in some sense that there is commonly upon General metrics, and that is also about how to be able to quickly spin our view contract and be able to validate each contract. That's why, I think, like, for example, what we work on the simulations, is important, is that we can actually simulate ideas and be able to support a better unformed buildings and evaluation support.

Oh wait, agree with you, Michael Buckley.

Speaker 3   08:17  
One more seasoning clients, like, what do you consider evaluation and and is that a definition the same? So I allow sometimes. Okay, so we've gone pretty good at evaluating models. Why does the valuation become dramatically harder once you turn a model into engagement? Oh yeah. Um.

Speaker 2   08:43  
I think so, and I think eval's the most you think of these end to end compilation tasks. So, in some sense, that's very simple to validate, you think. Like, for example, when you saw the GitHub issue, you might use unit tests to validate, uh. The issue was about, like, sold successfully.

I think one very fun thing with ancient nowadays is that they can cheat in very many ways. So, for example, a very simple thing is, you know, you take an existing GitHub issue. You give it two called code, and you ask, please solve this, but you know call code cannot reach you still get up in the internet, so you know it retrieves the original, like, maybe that was a public question that already fixed that issue from a human retrieves that test that out.

So, obviously, it didn't. Um, and so you can be like, all right, I'm gonna blog internet. Oh, that's actually what we did. Our program bench very recently. We really wanted to have internet to have like a more realistic workflow, but there was so much cheating. We were, like, all right, we pumped it up.

We have vlogged internet that still did not prevent the model from cheating, because what it did was speculate, um, specifically, sonnet was basically speculating, like, all right, I'm an agent. I don't currently have internet, but maybe you know, after I submit my solution, when you? That, so there's maybe that server actually has internet.

So, what Claude did was basically sneaking in download commands into its solution that, you know, it didn't have internet during that time. But when you evaluate it, which we actually did with internet working for the reasons, no, it was download the truth, like the the like, the original solution from the internet, and something down so cheating Behavior super tricky with agents.

And you know, it puts you in a bad spot because? You know, you don't want to lock down on your H and all that much. You want to have it like as free as possible, so it can really live up to its biggest potential. But the more like, the more unconstrained you, you phrase your task.

The more you expose yourself to what you think, and there's many more ways to achieve that. Just talk my head.

Speaker 4   10:42  
By the way of people, we love playing mobile cards and see all their things. It's scary, um, you can see all like, unfortunately, you know, even before you get to, like the more, um. You know, like that stuff, obviously matters. If you're you're building like Advanced benchmarks and best models and things like that, um?

Even before you get to that sort of esoteric stuff, I think we were kind of surfing around this in in the the last, uh, answer is like. We're fundamentally trying to evaluate something that's non-deterministic, it, you know, it's, it's, you know, making up his mind as it goes along, right?

That's the point. Um. And. You're fundamentally. Trying to evaluate evaluated on a space that is probably inherently very highly dimensional. Um, meaning that, like, there's all sorts of different types of inputs that this thing might have to handle, you know? So, what that basically boils down to is like, you can't rely on these sort of static, offline data sets and just sort of build content.

You have to put the thing in production, see how it behaves, and then have, like, online evaluation streaming through on live data to get even any sense of what the data distribution looks like. Um, and like, whether it behaves well, so it's sort of a very different workflow than the traditional ml1, where it's like, well, yeah, maybe you build a a?

Stick, you create an initial Benchmark. You'll come to Benchmark, you deploy it, you create it better when you help plan to be deploy it, you have to put the same in prop. First of all, to figure out how to spit and second of all to understand what the data distribution even looks like at all, and then from there on it's, it's still really, really hard.

And, like, you know, I think you know a lot more about it. So, that sounds good. Yeah,

Speaker 6   12:17  
I think like a traditionally when we say model, right? Sometimes, like, you just add a different things on top of the harness. Okay. You can take a base model. You can't give it an instructions. You can go in MD files. You can give it different tools and the inventory that it can use in some way.

You can always give it some domain knowledge or problems, right? So, this is how easy it is to build an agent basics, but the hard following is writing. A you don't really know how the agent would perform until they're really hit the production and talk to your real users.

So, in this process, it's really there are. Something that we can't do before production. Are you an after production in order to have better visibility about the agent's ability of behavior? Alice, sort of what we say, what we want to do evaluation off. You can never do, you know, perfect distribution of the user we're using users are changing as well, all right, you.

You might have a new product released, and everybody's asking about this new product, there might be a new events coming and your user distribution changes, because then you launch this new product, for example. Or whatever, and a new continent, and they're speaking into real languages. So, things are changing, so there's no ground truths or a perfect coverage in reality, because this is a real world.

So, what you can't do is really think about the violation as an involving process. So, so I curse the ice wants to connect with these estimates, and your testing cases is not static. It is truly involved me over time as well, whether you're a new capabilities in. Engine for new tools now, so improven all the foundational models, and at the same time, how your users are using the agents.

So these are all factors you need or automatically pick into considerations in changing your tasking cases. So, that's why the government is also thinking about the self-improving agents and here, because the violation is just once back to know what's going on with the agent. And most important part is, how can you improve the agents?

On the problems that we discovered based on the data that the user generated for you, right? So, these days, many people have so many traces and who log

Speaker 4   14:35  
In, but they don't know how they have a look at it. They just keep it as it is, and the real value in that, based on these kind of evaluation, metric or ways how we can reuse these cases to improve their agents, so that's why a lot of people are also looking into some improving agents, like, through reinforceable learning to repost training to improve your age.

Speaker 3   15:01  
Um, so I think that's a good segue to learn. That's question job, so have you seen an AI system perform exceptionally relevant testing and then failing fail in production? Uh, what happened?

Speaker 2   15:13  
All right, so I'm like more on the academic side. I don't run anything in production. I'm damn happy, I don't know, um. But maybe, I mean, I think we kind of already alluded to that, right? So I, I mostly design benchmarks, uh, for new capabilities. So my favorite Benchmark is a benchmark that starts at zero percent because you know, that means, you know, you can't turn into a product.

If it means, you know, uh, your model Builder, whoever trains the model you're using really fast, you know, to catch one? But what happens is like the second you release a benchmark out in the public, for example, program bench, and one week later, uh, you know, you have some data vendors that's going to reach out to everyone and say, like, hey, so we found this new Benchmark.

We created a lot of very similar tasks to that you know you want to train on that, and every single language model company, like a company they say, like, oh yes, you know, please? And so they basically train on very similar tasks from, like, you know, maybe like a week or a month after you release that, and so obviously that leads to very good field climbing.

They get better and better scores, um of your benchmark. Problem that happened with speed bench, for example. Um, and so in reality, if you have it like real users, um, using any system, there performance will always be worse than the benchmark Explorer. Because the Benchmark score is somewhat inflated, however.

This can be okay. Like, I think for sweet bench, it was okay, because in order to help climb sweevenge, it really had to like make models better exactly about what the users cared about and. You know that they test monoxide in many ways, but it was kind of diverse enough that, you know, climbing that Benchmark kind of still results in better user experience.

So, if you're creating like a new capability Benchmark, my advice would be, um. Make it very diverse. Make it very challenging, and so that even if someone is trying to benchmark it as long as they kind of, do it, right? Um. You know that it's um? You know, still increase use happens because language model providers.

Also, they don't want to over fit, like, in some, like, okay, like, they're like a little bit split, like they want to show very good Benchmark models, uh, Benchmark numbers in their model cars when they release, but they also don't want users to be very disappointed. So, like they don't try to cheat, but they also, you know, they try to balance these two things.

Yeah, yeah, I'm you're picking up on that a bit, um? You know? The.

Speaker 4   17:42  
So, you know, through all the the models out there are going to overfit to the the common benchmarks, but then, when you come up with your own domain specific benchmarks internally? The problem tends to be a it's expensive to do, and you need to get your product out there first, one fit, and B you suck at doing it because you're not a PhD and it's really hard.

So, basically, what you end up finding while at least ice up. You're doing how you can't speak for

Speaker 2   18:05  
Agonauts,

Speaker 4   18:05  
But um, but So basically. What you find is that, um, you know if you pull together that internal Benchmark, you're again overfitting it. And it's probably of poor quality until you get the thing into prod and start to be able to cheer it off. So that's that's kind of, um, you know?

Another

Speaker 7   18:18  
Thing on the, uh, you know, on the flip side of of? The public benchmark is going to cover their internal ones. They tend to be deficient in those ways.

Speaker 4   18:28  
So, we work with various different and provides customer rights as well, right? So in realities, people would just do things very unexpectedly, right? So it's very hard to create these corny pieces, so you haven't seen real world theme that, right? So, let's make a very popular kinds of agents.

I say customer service standings, so, uh, one example. For example, I always say is ready.

Speaker 6   18:53  
People would think about, like, for example, some of the functionalities and saying, like, the music comes come.

Speaker 4   18:58  
Say, hey, I want to return

Speaker 6   19:00  
My product, but this is a very simple request, but some of the HSV will fail. We kind of tested different kinds of agents out there because they're internally. There are various like a nuances of power retrained. I, for example, like there will be like, sort of, uh, when we think about it, if you purchase a thing, right?

If it, it hasn't shipped before we can. We're trying to be reality, cancel it. But a user would never know if, as a shift or not, they just want to return it. And then the model is calling it and saying, like, oh, there's nothing to return, okay, and then it wouldn't really think about it.

The returning actually means, cancel it. So, without actually having these count credit cases in your testing cases that your agent Builder well, engineer wouldn't think about these problems in the first place. So, that's why evaluation is really important. Israeli on domain knowledge as well. So, as we can borrow all servants similarly.

Agents like experience. It's really difficult to think out of your head as an engineer. The other way is to bring in, like, proud of me on a jurors or just for service experts, like you would call it smdu, subject matter and expert to really design these practices with you in order to be able to make sure that road test fees have all these quarter cases as well as you're happy.

Speaker 3   20:21  
Okay, last question before we open up some audience so? And the questions already. What is the most important unsolved problem agent evaluation today? So,

Speaker 2   20:34  
I have two candidates like, uh, I want us a little bit more like when you want to train and have kind of stuff. I think the toughest thing is pinpointing like a task failure on a specific action, right. There might be a hundred steps, uh, the thing fails in the end.

Like, I don't know. In my case, you know, there's a bug introducer background fix, you know, like, what action is to play? You need to know that in order to train like to perform RL or anything on that. Um, the second thing, and it's also more specific, I guess to Frontier evolves.

Like when you're designing a benchmark, um? Especially specifically for software engineering. Um, on the one hand, you want to be very kind of specific about what needs to be solved. Um, like, you want to get a lot of, like, uh, like you have to give a lot of kvs about, like, how to perform this task just so you can evaluate clearly.

Like, if you evaluate with unit tests, for example, and you want to implement a new feature, you know? Like, you have to give a lot of specs up front, because else you unit test that you created, they will not match whatever the age has

Speaker 4   21:37  
Produced, so you

Speaker 2   21:38  
Can't evaluate the feeling. But on the other hand, uh, giving all of these specs up front is totally not realistic, and it. Summits, the task much simpler, so you kind of stuck between, like, either I can make the task unfair, or I make it easy. And you know you want hard but fair, but it's kind of possible.

So that's for mice. Yeah, Workforce. What was actually been really

Speaker 4   22:02  
Resonant, even just for like commercial native building as well, run Globalance probable times, um. So, outside of those two, which I actually do, think they're probably the biggest ones, um, the next one on my list would be. Um.

Speaker 7   22:16  
Essentially figuring out how to connect your whatever you're doing online for experimentation and online evaluations to your offline experimentation and sort of open, right? Because you know again, whatever Benchmark you have is wrong, the distribution is wrong. And not only is it wrong, it's going to be wrong in different ways at different points in time.

So, which

Speaker 8   22:36  
Is even more fun of?

Speaker 5   22:39  
I got. Yeah, I shouldn't die anyway. Um,

Speaker 7   22:41  
So um, but the um? So, then sort of truing that up, right is, is? Really, really difficult? You know. And if you don't do that, then you essentially don't have any way of working on and improving your agent offline, right? All you can do is build it YOLO into prod and see what happens.

So that's, that's.

Speaker 6   23:03  
And to me, I think it's really about. You can't evaluate things on the surface faces. You have to also look into the pool halls and everything together, and also evaluate on this eight instead of just little traces. Where I'm talking about is, for example, you have assimilated environments. You're looking in terms of past completion about the state of what the task is completed.

For example, if you're talking about returning your product. The goal is really to look at the the database on the inventory. That's the thing is return. Or enough, instead of just looking at the traces and to all on the church. On top of it, I think this is really talking about variation of verification?

Well, you shouldn't be on the actual level and stable shouldn't be just like you're in a surface level about church. We'll open it up to on you.

Speaker 3   24:04  
Hi

Speaker 9   24:04  
Guys, thank you for the panel and thank

Speaker 3   24:07  
You. Yeah, I got a question. So, where do you guys stay on AI governance? Ai governance.

Speaker 2   24:25  
I

Speaker 4   24:26  
Think it's a very big topic in terms of governance, right? It's a it's about security about trustworthiness or reliabilities, and also like it on data security and everything. So, a lot of people are looking in the sort of more holistically. What are some best practice for that. And then, I agree, like within AI is actually harder.

Because, like, there are a lot of things like your data data week is, and all this could be really very problematic things when you train data, create models on customer data and things like that. What is the best policies like something that people can talk or engineer back through?

The stores really have?

Speaker 2   25:09  
And depending on survivation vigor, so I think that that's really going on.

Speaker 7   25:14  
What data are your customers? Can you train on? Can you build models on? Can you see, I mean, that's a huge area, right? It's something very clearly to governance around, um.

Speaker 8   25:25  
Yeah, otherwise, you may end up looking at the sensitive customer or something. We're very, very careful about, um. If you sort of flip around to, I think the big problems that I think we see our customers are seeing. It kind of boils under the three buckets, um, that that, you know, are related to something that could be considered governance police, um, one of them is, you know, just exploding token costs, right?

And how do people start to put policies around? Um, what models should be used for, for what types of things and control those. So, that's one. Uh, the second one is, um. Some sort of standardization around getting observability into the agents. If you have to go and instrument each agent individually.

That's very difficult. But then, if you don't do that, now you're losing this creative visibility to what with these things that are talking to your customers are doing right. So, how do you get sort of basically durability around the standard is, but it's the second one, and then the third one is.

Now you have this new set of security issues around, you know, data exfiltration. Things like that, um, you know, tax, right? These sorts of things that you didn't need to deal with before? So, how do you have some sort of standard violence or the security and so on that you know you want to wrap around these agents, right?

So, so those are kind of things that, um, you know? When you think about, like, Enterprise governance, you kind of need to go with some of your business? In addition to, uh, you know, what data the password to do? Thank you.

Hi, okay, I have two questions. I would love your thoughts on. How are you ensuring unbiasedness and safety? Uh, what AI is to or produce? In your businesses, like, whatever you do.

Speaker 2   27:11  
Number two is, what do you think are some of the best practices? All the approaches we shall came to build autonomously improving agents. Thank you.

Speaker 4   27:29  
Um, important. Maybe they're going to start answering the biases in safety side? So, uh, what we do is go, for example, like in our class, would you use the simulations so you can actually control attributes of your users, right? Everything else is the same you slow to like your area of living and things like that.

So then you can create synthetic traces of how a user put in triangles agent and then you kind of do the audits on the synthetic traces in each generate. So, this gives you a sort of unofactual bias quantifications. Safety is the same thing. You can also simulate these different environments like local distribution red teamings trying to see different users with different, like portal profiles, what it will look like, and they look.

How come? Uh, while you talk about yourself and proving a chance is also about in some sense. Like, not every data point, it's the same as other data points. Some are more useful than others, and you don't want to have repeated data points because it doesn't give you extra information.

Okay, so self-approving is also about how do you select a different world? So please have that data clients that you wanted to pick in terms of close screening. So, I think out is mostly what we saying, like the way you generation said data, which is great because you're no training on your real you.

There, and at the same time, how do you turn a digest? I don't data, I mean, so that the model of the train dog has more generalized ability, too.

Speaker 10   29:02  
So I had a question about you mentioned the government mistake. I want to emphasis still have in evaluation so. When you're having a cyber metrics as you said, no deterministic. Abstract results in your knowledge versus some narrative domestic veterans like latency, global, and what was next. How do you find the balance when you put something in an option, like, how do you measure the success of?

Um, is

Speaker 3   29:35  
It based on different lines based on different term? Like, how do you?

Speaker 10   29:43  
Uh, yeah, so?

Speaker 7   29:48  
There's kind of a

Speaker 2   29:48  
Cold difference

Speaker 7   29:49  
There. I mean, the I think the examples you mentioned around, like latency, like error race, things like that, like, you still need those right, and they don't tend to look too different. Um, I think the the understanding to me is, you know, what about the the specific things that your agent is doing?

Can you matter in a deterministic way versus non-deterministic way? Um, so you know a deterministic eval, for instance, might be if you have a, you know, a canned sort of golden data set? And you know, um, for a given interaction? What tools should have been selected? And you can say, yes, it selected those tools, right?

That's something that's deterministic. This is more offline than online, but I can't think of it on my example. That sort of thing right now, um? The the the non-deterministic ones are generally going to come from when you're using some Ln judge to actually create the evaluation feature. Um, and in general, if you can think of a way to do deterministically, you should do a deterministically, because now you have one less layer of, um, you know, ghosts in the machine?

Speaker 8   30:50  
Um, it's a reason about, and it's just cheaper. So, like, basically, um? You know, a lot of the way that the way that I've seen this breakdown in practice, at least for me. A lot of times is, I'll just like wrap the crappiest judge I can think of around the thing, put it in Prague, get a sense for how it behaves, and I realize, oh wait, I can measure like X1 and Z to termistically, and then I go and do that.

So,

Speaker 7   31:09  
Um, so, yeah, the short version is, like, try to do deterministically if you can, and if you can't, at first, like, let the judge out there and then like, think about it some more with data, and then try to do something good, so. And then once you realize you can't then just accept it in two years.

Speaker 5   31:29  
I'll be next. I have a question about evaluation design, so getting started. So, let's say, I just read my agent. And we very lovely data from start monitoring all right. You send your strategy, create my interest at some point. Maybe there is something that you missed?

Speaker 7   31:50  
Okay, now the money, but getting started and you have interesting standards. It takes time to be like a database, and you cannot mind it, I think I have a server and the camera monitor that I need. We don't have that for application, at least I'm not aware, how do you get started?

Like, what's the best practice? And you know how? Also, the same way, just know this image, but you everything's not such a thing of over monitoring. But there is every thing of overevaluated, so? You also avoid that because they couldn't just pay a thousand evaluation into very bright. So sorry, it's twofold, but they want you to take a look.

Speaker 4   32:30  
How much I can answer some questions, I think, like, there are evaluation. There's an offline validation and also the online package. So, how am I evaluation because you also care about hospitals? Your basically every tracing other, you have to do the valuation or so. Sometimes people do like a safe parts, right?

If you capture it, you can stop it right there, and so you can do something like, back up and request. So, um, I think, like, for offline, is also like, you have to design the metric together. Was your product? As like?

Speaker 6   33:34  
Zero one okay, because either yes or not, nothing in between. Otherwise, it's just harder to annotate as well.

Speaker 4   33:42  
So, I think that these are usually these are like a good practice in general, but in in terms of how many you want to do, what is important. Sometimes it goes to the policies, and it gets begun engineering things

Speaker 6   33:56  
Like, but in general, I think, like, test completion, or like, this past successor or not is the most important thing, and so.

Speaker 4   34:04  
Parts of it. It's really about wrinkle, exploring things and

Speaker 3   34:07  
Safety

Speaker 4   34:07  
Things that you you put on top. And now, you probably also care about, like, for so many years, so that's like the security teams also hear us about. So, these are sort of the major things that we usually design, and then I'll tell you violation if you run these offline so you can do more of these things, your judge can be slower.

Your judge can be more comprehensive, but do online ones you want to have a very minimal set. And then you wanted to know. How to use some formula as well? If you don't want to do anything? Since I was a distinction between like.

Speaker 2   34:41  
You might want signals to improve your system versus just a valiant how well it works, right? Um, sometimes it's very simple to figure out if something is working, but it's very hard to determine. You know, if it doesn't work, what's broken, right? So

Speaker 3   34:56  
Those are two different pairs of signals tonight, I think usually.

Speaker 2   34:59  
For Asians, figuring out what kind of what exactly went wrong and why your main metric is bad requires adding a lot more other metrics. Um, one thing, like the other thing? Um, I actually think there's like a big mistake that people do when they design academic benchmines, just that they give you like 10 different sports, right?

They they write their paper, uh, you know they? They pick their favorite topic, uh? And then they value different models, and they give you 10 numbers from each. Like, how you know? I just want to go there. I want to see, you know? Which model is best at selecting my favorite ice cream?

I don't know. I don't want to have, like, you know, 10 metrics for that, I just want to be like. Talk to chickadee, talk to Paul, I don't know. One thing you can do is very simply. I mean, if you have all of these different signals and you don't know how to read them, just add them together.

Have one number, um, if you want to be more clever, be slightly more clever. But, uh, I think, in the end, if it's a human looking at the dashboard. Um, sometimes this can actually be very effective to just aggregate like a bunch of these, like numbers, and like, you know, and then you know, if that number unexpectedly, like, you have to ask yourself, like, kind of, um, if this number like a flag that warns me if something goes wrong.

And then I look into the details, but like, don't overwhelm yourself. Like, too many numbers think of something simple.

Speaker 8   36:12  
Yeah, yeah, um, actually, just say that. Beside, like, we are picking a single like authorization metric and and understanding that, and designing three valorem is important. And then the the coming around. Avoiding, you know, using binary labels, unless you have enough data and enough statistical knowledge to actually calibrate what you've got like, you know, just the state designer interface, then your why would be a lot easier.

The only thing I'd add other than that is that that in here mentioned was, um, error analysis on compression traces, right. So, like, basically, um? You were going to want to sit down? In front of, like, a, you know, say, randomly sampled set of like 50 200 traces with your product manager, right, with your team and just like, go through detrace in detail and figure out what's going on.

Uh, you find it all sorts of interesting things that way. Um, and then you know other data. Actually, we've actually developed some skills and stuff to make that easier with our products that that are helpful for, like, first pass, analyzes, and like, cut down some of the time, but like, there's just nothing that gets you away from just like you have to spend some time like staring at every span in the trace and and you find out.

Oh, wait a minute. Why is it calling that tool 20 times, but what like, you know you find all something? Let's see how to do something. Thank you. Back there. And then we'll go. Okay, does it work?

Speaker 9   37:56  
So, I have a question about well.

Speaker 3   38:08  
But six months ago, the models were state-of-the-art. But now, as great, how do you keep up with the emails and the promotics like cutting, cutting wall. How do you keep up with all the change, the fast paced change, because once you pay your emails to a point where they're simply.

The model is the best, you know. Three months ago, like it feels like you can never.

Speaker 8   38:38  
Really cheap, um?

Speaker 5   38:40  
So, how do you think that advice we should add? Yeah, so that's why we, the important

Speaker 4   38:46  
Thing is that you wanted to have scenario based. Evaluation. It's not just who that test, right? It's like, oh, I want the the user wants to do certain things with the agent. The agent can succeed on death so that the user kind of doesn't change, and then your agent can swap a bottle and add different tools, and then we're just looking at is your agent can complete your map, and then you can't do side by side evaluations on for the same goal, the same profile we use her.

They can actually assume it or not, right? So that is. Fair in comparison. So, you can't just look at the sort of a step-by-step alcohol if you look at the interaction.

Speaker 7   39:27  
You know, just as a real concrete to that with that, that that's the thing. We actually do a data dog. We have a set of scenarios that represent, um, like investigations, right, like, yeah, SRE style investigations? I'll use the labels on them. It's, you know, two or three sentence summary of what went wrong and moving for the agent to produce a summary that looks like that right judges the evaluation.

So now, when a new model comes out, you can just swap the model out and say, hey, are we doing better on this massive set of scenarios? Are we not which ones are we doing better on which are weren't so. You're keeping those scenarios agnostic of details of models is important, so you have more specific email or emails emails them.

Our model to the Diablo?

Speaker 8   40:10  
That's why you find it so that, like if you swap the models out if it's an entire process, okay? Multi-agent system. If you're swapping, the model is out sometimes.

Speaker 7   40:23  
Yeah, it does, but that's that's kind of. The point is, if the scenario is well designed, like, like, in this case, a scenario is essentially. I guess the way to be a little more specific than in this case. The scenario is, uh, all of the Telemetry that, like, would go at the investigation on one side, right, essentially as the input archive.

And it's like, uh, um, and the output is, well, what was the outcome of the investigation? And that output should be the same, whether a human? Not, it does it. Whether a fine-tuned model does it, whether a foundation model from six months ago, does it versus the foundation model for today.

It's just input output, right? And so, it's agnostic. The scenario is these high-level scenario VC valves are agnostic to the details of a model, even if you do have more specific ones that aren't and pulling together those types of scenarios. You see, those is incredibly important for any, like, really expensive agent, because that's the only way you would be called.

I think the the biggest problem, um? When you're just switching models, is that you have like this confounder, which is, like, the agent harness that you're also having?

Speaker 2   41:26  
And finally, I would say, the stronger the model gets, the simpler your harness should look. Like, because you don't want to over constrain your model in any way. So, for example, like two years ago, and like speed bench was still, you know, at, like, you know, I don't know.

10 and people didn't want to work on it because they thought it was too hard and too challenging. For example, um, the first agent. Uh, we're actually like delivering on on that. And, like, we're starting to help. I'm there. We're like, very, very complicated. And it had, like, a lot of like eccentric tools, which were all hand, uh, engineer.

Um, now, two years later, I would say. Most Asians. They don't need any tools, like, at least in software engineering, if they already have access to your comment line. And they can run any bash command anyway. You know, why? Like, they don't need a right command. They don't need a real command.

They don't need, you know, any specifically assigned things. So, that's a clear thing. Like, okay, there's other reasons why you might still want to have that, like, permission, stuff, and so on. But, um. Basically, the capabilities went up to the point that, where all of this, you know, additional scaffold that we originally gave to the model.

It's no longer necessary, and it's hurting your performance problem. There might be other reasons to keep it, but like performance is probably not one of them, so you know if you never. You know, try to evaluate some different scaffolds on it. They might be, you know, stack of symptoms at all.

All right, we're good two in the back. Just remember, hold it very close. I, um, I just wanted to give each of your thoughts, um.

Speaker 10   42:57  
With respect to eval's designed for a single agent system. What do you guys think about as that migrates to a multitasking system?

Yeah.

Speaker 6   43:14  
So,

Speaker 3   43:15  
I think the depressing thing so far is that as cool as multi-agents are most benchmarks, they don't help you like, for example, speed bench, which has been around for a long time. People have tried and maybe temporarily like multi-aging systems for a bedtime, but then models got better. And you know, like all that beautiful, scaffold engineering mustn't work that much anymore.

Um, so it's actually. I think quite hard to find benchmarks that really require multi-agence, maybe program bench that we just released, might be one of them. Um, but like anthropic in the system count, they reported on it. And if anything, they don't gain that much by by using multi-agents.

Um. So, you just have to ask yourself, like, why would a multi-asia system you know work better here? Is it because you have so much context to to ingest, for example, that you know you want to have multiple sub agents that kind of, like, pre-compress information, and you don't kind of pollutely context window.

But on the other hand, context Windows of modern language models like they are ginormous, right? Like, you have a million tokens like, um, if you don't feel like all of the information that you could have, like, you know, flat set contacts when a while we have mounted, so I don't know, I I?

I would say for myself, worse? Single ages are quite good. I think one thing like, to me, conceptually multi-agents. Oftentimes are about context management.

Or are about a very specific Instructions, or maybe it's like an observability thing that you really want to divide up the workflow in in different stages that, at least from my point of view for, for very, very challenging tasks. Um, you have to work very hard to make multi-agents people.

Speaker 7   45:01  
But

Speaker 6   45:01  
They're

Speaker 7   45:02  
They're. Our specific news uses multi-agents are really necessary. For example, data parenthesis issues. There are assert an agents that processes can only accessory and data and other agents working out. And also there is a negotiation process sometimes, so you reply somebody just to be an emotion for a collective intelligence, like the, for example, engage settings, right, whereas avoiding and negotiate with other teams to swap wall material, materials, and things?

Or occupy different characteries like portrayed in their current price, so I think it was really about a use cases, but currently most of the people are using agents for utility practices like codings and stuff like that that I sell designing to print and turns out like your operation-based stuff, right.

For example, we are seeing people using like our agents to do under negotiations, right, so procurement and Pros? The question is about, there is. Contemption between the two. It's not always co-operative that everyone has its own. Gender is not shared with older people, and it applies like multi-agents. So, that's why these areas are more interesting in terms of using multi-agents and people create eventualizer and the most popular when it's echoing these out gaming studies, you're operating in teams, and you have to prepare juries are receiving different roles, and they have a transaibly different reward as well.

But Really, when you're measuring it, and you're also trying to use certain rewards as a collectible robot. So, for example, we are in the same team and you collectively need to win this game, or you're a e-commerce company. There are a couple of people competing with you and selling a specific product.

How do you optimize as an organization, for example, a company like the e-commerce company you're running? There are people doing infiltrators people doing marketing. There are people doing pricing and things like that, right? So they all have their own kpis. But collectively. As a corporations, they don't have their reward as well.

So, you see, this kind of tests are very specific that all pages can benefit, and then usually it's a reward. The violation is a design around the podcast.

Hey, one more question back here.

Speaker 8   47:23  
Thank you\! I want to confines to the first questions and keep you guys loved at night. I think I'm here, like, is this? Hospital, important to keep foreign. The bar or quality Improvement in a nurse in the scenario. Like, if we have agents and you just could choose whoever approach that would work and participate, validating final results, and probably important.

It is, do

Speaker 3   47:56  
We still need to keep, like, what could go on, what goes well, what do things about what you are?

Um. I mean, I think the even more important than it's been, right? Um.

Speaker 5   48:15  
Surely the agents can write a lot of code, right? They can change things, um?

Speaker 8   48:21  
But how do you know if it's getting better or worse, right? Unless you have some optimization function and some data to support it. So if I understood if I understood the question correctly, or did I miss something,

Speaker 5   48:33  
Uh, sorry? Like, if we could have like self-plugging right, solve it, correct? Then, how important is this state for us to understand? What's wrong, or we could just realize

Speaker 8   48:45  
Gotcha gotcha? Yeah, yeah. I, I see what you're saying, yeah. Right, so maybe someday it will be less important. But right now, it's still really important because. You know when the whatever is doing the the there's kind of a couple things? First of all, if you look in like deploying software in like a commercial setting.

There's still a lot of validation steps that just you know are in one way or another, just human driven, right? And so, um, if you deploy some agent to production? The team that built is still accountable for it, right? Not, not the notification, right? And so, um, no matter how much people you have in place.

There are things that are slip past it, so you have to understand what the agent is doing to understand those things that sort of slip through all the layers of cheese, right, or whatever we go for. It is. That's literally one of the problem uses by the bunch of slices of cheese and some stuff gets thrawls.

Um, so, so it's, it's still really, really important.

Speaker 7   49:49  
For that point of view, and then it's also important when you're running any of these optimization Loops. Well, what happens when it stops climbing, right, like, or what happens if it starts going down? We expect it to go up.

Speaker 8   50:01  
So, in just an example, one of the things we're actually working on. Now, for, for the product that I'm building is.

Speaker 7   50:07  
It's basically sort of this Auto experiment that it'll take a contraction traces, it'll you know, the agent will ask you a little bit of information, um, then it'll set up an experiment for you, and I'll start hill climbing on it. But then, what we

Speaker 4   50:17  
Show you is every iteration well. Which prices do you know which ones did it work on? Which didn't it, like, you know? Why did the the you know obsidization function developers down? So that way you can troubleshoot it, uh, if it's not doing the right direction. So, so I think it's important.

I mean, I think one other fundamental thing, um, when we talk about all these edge cases is? That.

Speaker 3   50:41  
You know if you're able to give infinite context. Like all, all the possible specification that you would need to give to the agent if you could give that upfront, then maybe this could work, but in reality. Um, I think it's you know. And before, I think it's just so hard to to find edge cases beforehand and.

In the end, it's a human who has to make these decisions because this system you know is

Speaker 2   51:05  
Fitted on a human on a use case for humans, right? So, we are the, you know, it's like, you know, if you have AI design, you know your house for you, it can't do it right because you have to decide what color the wall should be. The AI can't decide, you know what?

I've all colors, so there's a million decisions you don't even know which decisions they are before and. Um, and so fundamentally, I think, oftentimes, I mean, for example, see LMS at church or agents kind of misbehaving in any kind of way. Uh, it's often because there's certain specification aspects that we aren't missing, or they are not clear after you are.

And that's what humans are for, and nobody can possibly do that in their way. Same way that I come to sign the house with my neighbor, right? Because I'm not my neighbor, so?

Speaker 4   51:50  
Yeah, I think it will cost analysis right now. As you have, most age woman is trying to do it because right now, a lot of times like you have to fix the tool you have with certain things. People are still not very comfortable to let the clean agents keep you in themselves without the approval.

Especially, these are critical connections systems. So, right now, the CEO replies, like, understanding or human approvals needs to be the final line of the person pushing the reproduction.

Speaker 8   52:22  
Hello, dear, um, I mean products. So, I want to ask for UAT, and I trust you in the UIT for agents. So, compared to a normal AI. Know what are special about agency and any tools to have a sufficient support?

Speaker 4   52:45  
Um, yeah, so it's based on where you have, and you know, um, so

Speaker 10   52:52  
I think I don't at the same, but I don't think anything. Fundamentally, changes around like, you

Speaker 2   52:58  
Know, the nature of sort of, uh, user acceptance testing, um, you have to think through what, what's the user actually doing with this? And and what is successful, like? Um.

Speaker 8   53:09  
You know, and then you would be, you know, you know, do the customer service? For example, you know. So, now you're dealing with this, right? So, maybe it's going to give you a differential first time you asked in a second? You know. So, I think that that's kind of the real main difference is just the level of non-determinism is much higher.

Um. You know? Um.

Speaker 4   53:31  
Which is kind of why sort of have having a human like human Loop that these things ends up mattering a lot. The other thing that's interesting is sort of a more technical note is like, once you understand, like, what good is right? What good is your user point of you, um?

You can then figure out ways to generally figure at least automate that, um, so? Uh, you know, this is called various things. But, like, you know, like, satisfaction, or like, um, test completion, right, basically? Did the agent do the thing it was meant to do is going to be specific to your domain, but once you know what that is, you can create an LLM judge to measure it based on the traces that come through sampler traces.

And, you know, keep an eye on those as they come through as sort of a semi automated line of offense. But then, when U? Value of you on the testing side is every time that that eval pops up red is go and look and figure out why.

So? I'd like to write your opinion as a question sorry. Yeah, I want to go a stir fry evaluation and.

Speaker 10   54:43  
Think about, uh, what an agent can actually act on, and what kind of task it should take out, should it be sized only or should it actually go into the task and work on the actual thing? How do you calibrate an agent or? Road specific agent to recite what task it should take up.

So,

Speaker 4   55:05  
Usually when you design a major product, right? So, it's usually in common people's sort of a designing from. So, what the agent's functionality should be, but your reality. Sometimes you release the agent, people are just gonna do whatever they want to do anyway. So, that's why there is always like a sort of outer distribution samples you might get.

So, that's why, as we talked about before, once you get a production data, you want it to actually extract what we wanted to do and what it's considered in scope and what is considered old school, and by analyzing it, you might want to actually change those kind of specifications as well.

Because people are more interested in the bees instead of other things to be over joint design with them.

Speaker 3   55:46  
I'm not sure. Oh, were you asking about, like, um, ages, selecting their own task, or finding what they want to do themselves? What do you want to do downstairs? Oh, okay. So? I think the bad news is that H's not really bad at deciding you know what should be done right, and that brings us back kind of to the decision question.

So, um, we, we're actually working on a benchmark called. Coach class. Like, I'm so short, it's like two Asians writing their own code phase and then the code base is, like, I don't know, like a trading simulator, and you look at what code base you know gets the more more money or something like that.

And so, for this specific thing. You don't have specific tasks. We literally, just, you know, explain, like the game or the simulator to the agent and tell it like, you know, whatever you do, you know, build. The best thing that does next, which is a very like high level goal.

Um, and we tell, like you can look at logs, you know, we run some of these simulations for you. You can analyze what went wrong, you know. Find the bottom Knights, and so on and. Like, that's just not trained right now to pick up plastic sales. They are very much trained to, you know, have a very specific task, like, execute that, and I found it, and there's like a lot of pathologies that can happen, like one of them is.

For example, if you have like a a stocking code base for this task. They will never think about, like, completely changing it. Because they have trained against them. Like, then, they will just pile back things and work around on top of another. Um, they are terrible at, like, looking through logs like, like, basically the expectation if you give them a log, is that there's an exception in there, and then they need to trace back with an exception is coming from.

But if it's like an open-ended statistical game, and you're like, you know, there's like a million steps in the end, like the result is loss, and they need to find out why they lost. So, this is really cool, though, you know, as someone who's interested. So, a bench fracture making models better because that means that's something to improve.

Yeah, let's say. You're trying to create a a organization and you've got certain. We're all specific agents created, and would it be ideal if?

Speaker 10   57:59  
Bring those hiddens on how people have people in real world have acted in those certain situations and. Maybe you apply some reinforcement running on the whole thing and? Being able to draw judge on what to what? Um, but uh, decision to take in under those circumstances. Yeah, I, I

Speaker 3   58:24  
Think that's super interesting. I mean, I would like to have set the system tell me everything. I think it's very easy to do on estimate. The amount of like content literature seven hour frames in the same way that you know if you ask Chetship to you, you know, or Facebook, and it was still available to write an email for you.

It's impossible, like, it's just. I mean, even if you put a page of context in it, like, oftentimes, you'll find like it just gets all the nuances, right? Because it doesn't have the context, so I mean, I would love to have that. I think it's very challenging. It's very cool, like, um, you know, look for challenging things.

To do.

Speaker 9   58:56  
Thank you all so much for this very insightful talk. Um, I curious if any of you, you have seen any interesting or impressive examples of companies using agency the consumer syntax space?

Speaker 5   59:11  
If not, I'm curious to share with us on how companies should think about, like learning and maintaining users trust, when using agents to interact with users. Thank you.

Yeah, I think like a finance in general is a compliance area, but we definitely have seen people are using, um.

Speaker 7   59:34  
I always say Indiana models in general to do. Tasks are more easy to verify, for

Speaker 5   59:40  
Example,

Speaker 7   59:40  
Fraud detection, right? That was like a traditional problem. Many people might be working on it in the old days. Now, people are transitioning into more agentative way. I'll do verifications,

Speaker 6   59:50  
So I've seen other areas like mortgage underwriting.

Speaker 8   59:55  
Yes,

Speaker 6   59:55  
And these are usually just information calibration information extractions, and this is basic the word field. Agents, especially animals who actually consume a lot of information. There is like PDF, Dimensions, and so on. You can't do a lot of these streamlined, and you can sort of do consolidations. So I think like there are a lot of space, especially in finance when there are few boards I

Speaker 8   1:00:22  
Really

Speaker 6   1:00:22  
Do see, there's a huge Improvement of who we can and especially consumer like, what good about EIS using my space, right? You can do personalization. You have more contacts with this. Like Financial choices, and so on. It could be, I see many people were talking about, like, these kind of individual Financial advisors have people looking into.

There is also individual.

Speaker 4   1:00:45  
Um, like, they're asset plannings or things like that consumer space is actually very good area in general for AI because you have passive data, a massive like a trajectory that you can learn and optimize your system. Coinbase registered in Rai that?

Speaker 8   1:01:06  
Point is registered in agent.

We have one more question in the back. Yeah, so this will be the final question. You want to do is to?

Speaker 5   1:01:19  
Hi, thank you all for the

Speaker 3   1:01:21  
Pleasure. You're a little bit

Speaker 2   1:01:25  
Quiet.

Speaker 5   1:01:26  
Oh sorry, thank you for the amazing though. Um, I think, uh, when the gentleman in the middle mentioned the, unlike offline discrepancy and how they right, no, we should. It's kind of.

Speaker 2   1:01:41  
So, then you're going to be prone to out of description, kind of issues. I'm just wondering right now as far as like, best practices go? Is it kind of the case where you would have multiple different models and like harnesses available when you're starting to Route it like different prompts and different queries that then be rather than different agents because the expected reward could be different in different models, you know, faster.

Company's objective, it seems to be a probable just as well, uh. Yeah, I mean, there's. There's kind of a couple of answers to that question. One is, um, so, yeah, um, there are certainly.

Speaker 6   1:02:18  
Definition. It's it's kind of loose here. It's like it was a thing that has a single context from Noah, but, uh. But there are certainly systems that I've seen, where, um?

Speaker 8   1:02:29  
Either queries electron to be routed in different models for cost reasons, or where there's a bunch of short element interactions that come together in some larger anything, and they're out at different ones, so that's one thing. The other thing that's actually really interesting is, and that's kind of more interesting to me is the.

Um. Uh, you know, I mean, the relationship of, like online experiments a, b tests, um?

Speaker 7   1:02:53  
To like online evaluations, and then essentially offline experiences there all tend to be different layers of the tool staff right now. Um, but what we're starting to see, you know, teams doing that are more sophisticated. And you know, they'll a b tests like different model versions on, um, you know, sort of, they'll maybe test.

I mean, the same agent with every model or just a different harness, the harness that often matters more right nowadays. Um, especially too much of it, um, so you know we'll see them. Do those sorts of tests and then they'll want to look at a sort of evaluation metrics that are fundamentally they're online ull's, and then they'll want to go and pull back on things so that AP test and they're offline data sets.

And then, they'll also make a decision. Oh, we're going to clip on the B side, right? So, so these things all kind of relate in some way that, um, I don't think you do this right now, with the product or something good. And I think you know that?

Speaker 1   1:03:51  
All right, cool. Um, I want to thank the audience for being very good at the whole interaction thing. Thank you, thank you\! You're amazing, countless. I'm moderator, and you may not. And um, it's been a great so, but we saw some pizza. There were drinks, make shelves at home.

We have until eight o'clock, right? Okay, and then we have to. Okay, thank you.

Yeah, yeah.