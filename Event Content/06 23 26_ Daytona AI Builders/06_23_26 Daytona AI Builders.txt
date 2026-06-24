
With the presentations and later Builder, we will have more network traffic sessions.

[Speaker 1]
Uh, and then just information about toilets, restaurants, or there.

Okay, uh, good evening. So, another?

Here in data local office when we work. Um, huge thanks to Toyota or cabinets, and of course, Laura, yeah.

And also huge thanks to Oracle for support cameras.

Um, okay.

[Speaker 2]
So, we have a. Uh, six interesting presentation tonight. I'll just have a huge slide, then we will kick off the presentation, um.

So, yeah, my name is Mariam. I'm a class manager at Daytona. Um. And agenda for him for today so? Will kick off with the presentation from my colleague Ahmed. From Daytona. Uh, and then it will be followed from Oracle team presentation and.

Black Smith will have presentation and to wrap up with Uncle browser. Um, okay.

[Speaker 1]
Uh, or if you want to connect with the psych Community, you can scan this your code.

Uh, and also. Uh, we have our Ambassador program, which called Victoria Pacer program. If you want to?

[Speaker 2]
And pass in the picture of this event. Write the blog post you can reach out to me and. I can help you. Okay, that's it for myself. And places.

[Speaker 1]
Um, hey everyone, I'm Muhammad. I'm your doctor as an engineer at Daytona. Um, we provide sandboxes AKA disposable computers for AI agents. And um, yeah, I'll be getting a demo today, but for that. We're going right into the demo, uh, I think it'd be a good idea to kind of, um.

Verifying like? Why a lot of you guys might have heard of different famous Fighters popping up recently, um? And I think it's confusing.

[Speaker 2]
If you're not familiar with, like, kind of nuances, understand, like, why is it? This new, I guess type of infrastructure, is coming up. Why not just use, like, like a DM on grow traditional hyperscaler? So, yeah. Yeah, that's that.

[Speaker 1]
Oh, it's cool, um, so basically, like?

[Speaker 3]
Every end of the infrastructure follows a different type of workload. So, like, for example, you have a persistent running server that needs a server class, no matter what time to pay. Um, these would be always on. Um, and so for that, you'd usually use bins. I'm obviously have Services as well.

Elementary Services which the quantum containers? There's a like a redis category database. Um, and there's also functions which might be triggered on an event, and there's no kind of like state to be reserved there. It's just whenever something happens in your app. You want, um, you want something to run?

And. Basically. Uh, that were disappears. After there's nothing saved usually.

[Speaker 1]
So now, like?

[Speaker 3]
With kind of how people are using coding agents. There's sort of a different pattern or difference. Type of workload. The currents, the current infrastructure performance aren't, is that they optimized for? Um, for example. A lot of new products need to get the user. A task or an agent Allies environment.

And it's not just a process. It's like a persistent session right. And inside that session, there might be. Code that gets generated from the agent from model. Maybe it needs

[Speaker 1]
Shell any file system, a browser.

[Speaker 3]
Um, you know, other different running services? Um and. As the agents and it works. That state needs to survive across on a bunch of episode tapes. Um.

And so, for that type of workload. These old choices that we had. Um, these are them are kind of missing some. So, like VMS, for example. Life cycle of Indian or kind of the? Oh wait, I guess you could say it's pretty heavy if you are. You know, in one environment, per user or per agent?

Um, because again, like I said, there's sort of made more so for long-running, persistent servers. Um, and so. Yeah, if you need an environment to like, start up really fast for an agent, for example. A regular VM. For the, it has isolation, but? You know high latency? There's also containers.

But they were, so containers are usually kind of built around packaging applications that are mostly trusted. So, like, these are apps that are written by users, uh, or written by humans. Um, and so. It's kind of. You assume it's like, trustworthy, not malicious Pope most of the time, but if the code is arbitrary, which a lot of times it is?

By an agent. Start writing it. There's kind of. Then, it becomes like untrustworthy, because especially if your agent has like web access. For example, whatever reads like? Um, some markdown file written somewhere and basically. I don't know. Remove system 32 or something. That's always something you don't want to have, so.

Um, containers. I have a shared kernel, so like?

[Speaker 1]
You lose the isolation, you gain what Lane to be the isolation VM. And then functions.

[Speaker 3]
Again, they're stateless. You saw, there's no kind of like criticism level you typically when using agents. So this new? It's kind of a new unit of. Um, I'm also impermanent that needs a combination. But it used to be awkward, um, or is kind of awkward to use one of those previous Solutions.

Basically needs to be isolated because you don't want your agents freaking out its container, you know? Um, affecting other other users. Um, and also like I said the the code that it writes is arbitrary. By definition, it also needs to be fast. Um, as users agents. Obviously, you don't want to wait too long for setup.

And easily stateful because work doesn't disappear. There's files, processes, logs the state of your browser computer and like partial progress. Um. And easily disposable because options. There's no reason for you to pay for if there's.

[Speaker 1]
Um, so that is the shape that deton that exposes? Um, basically. Getting every session or every agent, their own computer. I'm going to close this all three. Very easy to use API so. Um, is there any agent you have can get its own operating system? Compute resources. Obviously.

[Speaker 3]
Along with the NOS pencil reading like a desktop and browser, a file system. All that, um, and instead of talking about how easy it is, I'll just go ahead and show you guys so.

This is what our SUV

[Speaker 1]
Looks like. It's a business show, yeah. So, it's really just. In Port Daytona and then.

[Speaker 3]
Dot create. It's on a dot create. And then you can specify I'll go into this in more detail on this slides. But you can kind of configure how exactly you want that sample to be shaped as some code just to measure the performance around it.

I was going to remember this. We'll see how fast it is. There's some variants with this visually.

[Speaker 2]
It might take longer than it says because. This doesn't measure any.

Let's look.

[Speaker 1]
Okay, there you go, so this was created. I even milliseconds. Um, the generated paper URL. It's just a very like basic. Yeah, it's the consumer file anglo from the sandbox. Um, so typically this is a URL being served inside the sandbox. Um, it's a group that I can actually just create a new line.

We'll hit the. Let's see.

And then run that.

[Speaker 3]
Um, yeah. And then obviously. There's cleanup so? Because I labeled it. This, I'll give it this demo. Same modules label and I'll just clean out any sandboxes with that label.

I mean, it's just like, not complete.

[Speaker 1]
For the stigma demons.

And so specifically, the reason why, I guess. The like, the merge says. Computers for agents, we, our controls as composable computers agents, as it's not just a environment that gets code. So, like, you might think of a JavaScript isolate or an environment that kind of specifically executes python code or for yeah, JavaScript code.

Those are obviously a lot faster and a lot more lightweight, but they don't come with a OS cpu's. Time, so. Those those types of workloads and obviously run on Daytona sandboxes, but um.

Yeah, well, we're a lot more than than just put bucks.

Uh, oh, yeah. We also have computer use, so I think this one doesn't die. Um, it's gonna take a bit longer to start up because computer use. The plugin is loaded. Unless you actually use it on the same notes. But people in this works, I can show you guys.

Yeah, so, like I said, beautiful OS. Um, so this is me manually driving it.

You probably just have your agent do this instead, and just another time. Maybe watch what your Asian is doing, or have it record what it's doing? Which about that. That's I'll be blind later. That's everything that works this time.

Okay anyway?

Um, yeah, and. The composable part comes from how you can actually like.

I'm gonna zoom in this a little bit.

Um, hopefully you guys can see the code.

[Speaker 2]
Okay, that works.

Okay, I'm here so. Yeah, and what I. That's what I mean by there, because that's why the exact image.

[Speaker 1]
Um, any other site image from any registry. The exact amount of resources you want, so? Um, I want two cds, four gigs of this. Um, and any labels that I might want for my own app to use, and also I can set like, okay, after 15 minutes of no activity on the sandbox.

And I wanted to start. And then, after an hour after that, I want it to be fully believable. That way. Yeah, I don't think your idle compute.

I don't know if I'll time to run all of these Snippets, so I'll just like. Go into this little bit faster. Yeah, we also have snapshotting so. Um, if you build and you build a sandbox from an image the first time, it'll be. Uh, I won't be at us because it has.

Kind of, do that starting from scratch, but you sandbox it or snapshot of it. Um, it starts a lot faster, so this is.

So, this is using one of our default snapshots Daytona medium, and you'll see. Should start off because?

There's some variants here, but. Yeah. Now, we also the 14 features, so this is. Um. Is before King, not just from the biosystem state, but. Whatever you say as well. So, any process you have running that have? For example, with database or 30 like hit work tree. Those things are only those things aren't stored in the file system itself.

So? For that use case, you can snapshot both memory and file system State and then. Start, just stop the sandbox and start effect from that exact state, which. Uh, yeah. For the second time, we'll just move on. To the demo. Um, so? Everything is cool and all, but um, how do you use this?

How can you, I guess, benefit from this today? Um, there's one of the things you can do with our sandboxes. The one thing I like using it for is basically making my agents. Use my app in the sandbox and kind of prove their work. What I mean by that is like.

A lot of times, I ask an agent to implement this feature or fix this book. And then it tells me. Look at all these goods has passed, and I'm going to actually try to add, and it just doesn't work. And so. I was, like, okay, let me just ask the agent itself to use that app.

So, right here, I'm just just this, um, pretty simple demo app, where? Um, it's an insert integer. If I update the? Quantity here. Uh to 15. It looks like an updates on the front end, but can I refresh? It goes back to I'm 28, um, and so. I won't be able to do this live, unfortunately, but I pre-ran it completely, um?

I had. It's gonna ask my agent. Hey, um? Because there's this bug in my app where? Um, I'm going to add in an item. And it doesn't actually persist. So I just asked that to fix it, and It produced this video.

Which proves the butt picks, and I had to open up your own stuff. See, let me zoom. You can see this. All right. And here's my age approving from work, so it'll change. I'll see the 142. See that refreshes, and the property actually updates, so that's cool. Um, I can actually know that this works, and I don't have to go in and test that myself.

I can just see the video that I produce. And.

I know, it's it, I don't know. If you guys any of you guys, uh, like, I mean like nobody reads dogs nowadays, but uh, we sort of recently released this, uh, Daytona skill, um, if you guys want to basically tell your agent, like, hey? Um, or for whatever you guys want to.

I want to use Daytona cord your engine's skill. And that'll be a little bit about. How about how to use this? And we also have a. Startup program. Where we give three credits to. These startups. It's one of the iOS startup slash startups. If you guys want to sign up here basically, yeah, we get up to 50K.

If you're still up, and you just want to use Daytona for, for whatever reason. And yeah, pretty much it. If you guys any questions?

[Speaker 3]
Yeah, um, that's actually one of the biggest, like. Use cases right now. Oh yeah.

[Speaker 4]
Oh yeah, I would like to know how dahina has been used to evaluate different agents and how they are deployed inside of different Enterprise part. Yeah, yeah, good question, so?

[Speaker 1]
That's one of the biggest reasons why people use this Earth starting to become like the majority of. Out of spending on this one is. Um, these large-scale evals for enforcement learning, um? Basically. Uh, to just to kind of explain how it works. You usually? Of your closer gpus with an lln.

Running on it, making tool calls as they're working on tasks, and those tool calls need. Some compute environments are on, and because we're fast because you can spin up a lot of them at once we make for. We happen to be really good in construction for that, and so audit reinforcement learning.

Um, Labs startups use us to do their emails and stream their agents. For example, the biggest most level ones Harbor. If you guys have heard of terminal bench? Um, harder is a framework for catalyating agents. Made by the greatest internal bench and? Which is probably? Shameless plug right here.

[Speaker 3]
The default back-end for evaluations. Any basically? Terminal bench shapes. Um. Benchmark, so sweet bench. A lot of other ones exist.

[Speaker 1]
Yeah, like a list of adapters. Um, yeah, so that type of? Workload it? We're well suited for that, and then more and more people are some because.

Any other questions?

Um, so one of the example you showed was that I have example. They showed us. Uh, what about something that uses more mobile data frameworks like greater or Swift? Would be able to, I guess.

[Speaker 2]
Test that as well.

[Speaker 3]
Put up that kind of environment where it's able to have an Android simulator in that environment. And take screenshots and then make cool first. Um, to verify if the app is actually working. Yeah. You, are you asking, like?

[Speaker 1]
I'm asking if the sandbox is able to, I guess, to install those. Oh yeah. The three os's? Yeah, yeah, yeah, the same likes itself can, um, you mean, it's? Anything you want to install that can be installed on, like my next door windows? You can install under sandbox. Uh, does that answer your question or asking?

Are you asking if we support like Android OS samopsis? Okay, I was thinking of Android. We don't support that soon. So sorry. Okay, thank you very much. Thank you.

[Speaker 3]
So, next, we have

[Speaker 5]
Oracle team presenting.

[Speaker 2]
Ed Sheeran of tomorrow. Why Museum?

[Speaker 6]
In-Person experiences, and I feel like a lot of them have that I think different events. Uh, my name is.

[Speaker 2]
Jeremiah.

Is first of all whatever you just saw.

[Speaker 4]
I'm not saying that is the case, and there's a possibility

[Speaker 1]
Behind the scenesis. It has one of some stuff. It could be article AWS.

[Speaker 4]
So, that's what we will talk about, uh, anyone here, just like, show a fan in? Are you guys familiar of Oracle Cloud or invest in Canada? We had before, all right.

[Speaker 1]
Okay, so,

[Speaker 3]
First of all, when Cloud has been there for a while after, you guys know this is.

[Speaker 1]
But, as of right now, since last three or four years, the whole Dynamics has changed. The world is a history, and I say, well, I'm talking about technology and Cloud, nothing else.

[Speaker 4]
So, there was a time I'm not sure how many of you here have worked in that space, but when we were talking about moving the cloud. It was usually folks running an unfair data center, or they

[Speaker 6]
Have their own server, and the traditional model was. You will look at the capacity what I'm running, and I'm running X number of compute X number of memory

[Speaker 4]
Storage CPU your map because. And then.

[Speaker 7]
Commissioners come to the picture a lot about us, including us. We will start moving in. The discount should make

[Speaker 1]
It possible for use that economic works and the new vote from your long frame to cloud or

[Speaker 7]
Any other section. That thing is change. A new valuation model is not really focused on what you are running on. It doesn't matter how much asset your server has, it doesn't matter, how much is when you are moving to Cloud? Now, more and more customers are.

[Speaker 6]
This is my work though. What capacity I made on Cloud? It doesn't matter which I'm using 50 dollars or 50 processors on here. Maybe on the cloud I am making 25, and maybe I need 80. So those kind of consideration of the future now come here to hourly rate how much it will cost from your running on the cloud and how customers are looking

[Speaker 4]
Yeah. How much you will ask to run us as query wellness as a transaction and then obviously. But not the news since last few years. If you haven't.

[Speaker 3]
The whole supply chain, so capacity issues. Every calculator right now is deliver some issues.

[Speaker 4]
At a summary of storage or so, I like to say the equally data Center space. So, now, as a customer, everyone has to be considered. Yes, it's a good starting point for me today if they said, what do we have X or better? Will I have capacity if my business just grows and will I be able to be able to pass it in workplace?

And you know? So, keeping that in mind, obviously, there's to be the way we see. There's two type of cloud providers, which are emerging or looking at them, the ones who are prepared the ones who are actually mapping a workload to the cloud economics through the cloud, cycling, and also making sure that we have capacity over the government in 100 days ago.

And then there are still Club winners now, taking males who will rely on. Let's go. Okay, we'll make it. Okay, it may not be right sizing. It may not exactly work 15 years from now, but you have a great discount, and because so the guy who is not just the price.

It's actually the orbiting Freedom. How do I operate my business in the cloud? So, three things we should talk about today. I had a scientific picture in this likes. I don't think you have to understand, so we are trying to compose it in three things. One is oci yoci performance.

First, architecture was listed in 2016, 2015. The entire Focus was performance. It's not necessarily cost driven just because it was a soundtrack will make it cheaper to our work. Well, no, that was not the purposes a third person was. You get the right of. Moments, and you get a right place as much as all of us here.

I have a ton of serious leaders who are going to China. We would like everyone to run over here, and that's not where can happen. We understand that customers will have exhibited as a nature. There are times when you are running some things up on Trend to different clouds, and you need to have a multi-cloud setup at the end of the day so OCI, you know, the first one come up with that our processes?

With a lot of fiber and multi-compressibility and India, because the way we understand all of your builders of that space, Java is going to convert those circumstances.

[Speaker 1]
Anyone has any question I don't have to make an deal please and have no idea? So this is something briefly, which I know with. Again, if anyone is keeping track of that market, you will see the memory cost and their storage cost. As it appears a lot in last three, four years, significant people, computers becoming cheaper.

The memory is going really high for 50 people started right now. Was it? Okay, I'll give it closer. Thanks. Uh, the value shifting obviously from compute to system efficiency.

[Speaker 4]
Now, compared to what exactly what we used to deal with customer until four or five years back. Now, it's not just moving to Cloud, it's the efficiency.

[Speaker 1]
A cloud computing cost now rewards memory efficiency, not just running on cloud, which means even right now compared to last year. Today, when I talk to customers, it's not just. I'm using four posts and perino pics of memory. Can I get that? You know, CI, it doesn't matter. Does your application actually needs a little bits of money?

If yes, then there's a car, such as going like, if no, then let's afterwards, your application. Maybe it only needs 16 gigs of family. Why should you be paying five or five? And lastly, the network performance, given the AI space of the interest everyone has here. I'm sure you understand there's a ton of data movement, which is involved.

Your data Cycles are sitting in multiple data on-prem, but on the other databases, one of the other cloud provider. The egress cost right now is one of the most highest tasks for any customer moving data out of one Cloud to another. So, again, you know, CI. The when the cloud was designed, it kept into, uh, that thought process that the cost has to be, uh, minimal and minimal maximum message.

Uh, the workload type as I talked about and let me go through it. I'm sure all of you understand is no longer just running any application or in your Erp, CRM, or Healthcare application of the cloud. The kind of workloads have changed. All complex has a lot of India and I.T companies, including big names like Paramount, so there's a lot of this streaming, which happens a lot of video demand and the customers, which are immediately.

Yeah. These are all Global events hdki Systems. All of that requires faster performance at a lower cost, and more importantly, the network robot. The data movement has to be extremely extremely fast. So, here's what oci has done when OCI was originally introduced. There's number of things which we did was was granular, flexible infrastructure.

What it means is OCA was the first one which came up with the flex interest. What it means is, until then, take a name AWS, for example. They had fixed shapes if you have. If you want to stain up a VM on AWS? You will go with a certain compute.

Let's say you want four vcpu, and it will be attached with. 16 gigs of memory. Maybe you don't need that, but you have to have that now. If your application is never intensive and you need 32 gigs. You have to go to the next t-shirt size medium, large Excel, which means to get 32 gigs off memory.

You have to move to eight vcpu, even though you don't need that that directly impacts the economics of a remote cloud.

[Speaker 4]
Global Network across multiple data centers and across the globe. We also came up with bare metal a lot of times. Customers don't want to run shared public serving market? They would want a dedicated box for themselves, which they can virtualize. They can use their own hypervisor. I'll talk a little bit about the subsequent slides about distributed Cloud building blocks and obviously the price, which happened up in America.

So, this is a slide, which I really want to highlight. What happened at our location, the first one 2010? What you see was the gen1 of Cloud, which all the other clouds came out. They had knocked them and nothing wrong. Back then, the requirement was to rely on hypervisor, virtualize your physical Hardware, physical host, which is a huge beefy box and have multiple customers running on the same box with multiple VMS.

A ton of problems at that. What it means is a lot of resources. A lot of horsepower of that machine goes into virtualization. Both the storage and network emotionalization. Then there are security issues if one of the VM gets compromised. That can very easily get propagated to rest of the VMS, even though they are two different customers who are not in there.

So, what order initially did? We don't talk about it a lot nowadays, because that was talking again on order was the first one to come up with something called. What we did, was we physically separate?

[Speaker 1]
Network and storage virtualization in a different card, not running on the same system, but a different card, which involved now and for computer. Two things happen. First of all, now the physical box where all of you are creating VMS, it has hundred percent capacity. Nothing is being seen as an overhead, so if someone ends up abcp or Ato CPU, they get the entire hour all the time.

[Speaker 4]
And the second thing, because the networking and virtualization is now sitting on a different physical power. Yes, next level of security, which means even if a virtualization layer or network layer gets compromised.

This year in Ephrine, the reason this light is important is this year we took the next level. Now, a lot of other Cloud providers followed, and now they also have similar offer. Whether you call it Nitro or any other name, they also have moved on to our box authorization.

April, I believe early April. I think we announced excellent. Exel non is the next generation of Chip, which we are, including which are coming up with all the new oci footprint. So over here. What was happening is our Pakistanization from control and the smartnick on the other side, and there's a networking in between, and we were delivering somewhere around 2016 to 2018, we are delivering 25 bits of type of throughput.

That's a little long, bad enough. Given the AI space we are in atom of a jpki work or machine learning model training model, creation of that is happening. 25 this is nothing you are talking about Excel here, right? It's updated to be more. So, what, Etc, what we have done in Excelon is, I don't.

I think there's a diagram.

[Speaker 2]
Okay,

[Speaker 4]
Yeah, this is that country next year. So, this is where it was a separate ship ethernet, and this is your physical server multiple games. Different customers, I mean, and all the virtualization there is here. With Excelon. What we are doing is. Year on.

Gpu platform, at least we are delivering

[Speaker 1]
Up to 800 gigs of network robot. Now, that is what the must Market needs today. If you are working on a model training or even inferencing for that matter, you need at speed and the only way we all can decide that a speed is through XLR. The second part is global footage.

Again. Not to brag about it, but OCI was the first one was the first one to come up with multi-cloud architecture, so we have highest number, biggest number of data centers across the world. What it means is in your kind of workload when you are having data setting in silos and multiple locations, whether the same geography elsewhere in the world, and you don't want to move that data.

We have more data centers than any other program. We have public Cloud data centers. We have EU sovereign Cloud Data center and in U.S, we have 12 Cloud data centers. In addition to that, we also have two very, very unique offering. One is called dedicated Cloud region, which means if there's a customer who says, hey, I cannot.

I like your cloud, but I cannot run bucket client. I would like everything in my own building and my own data center behind my, your firewall. We literally copy paste our public data center. And create a physical data center for you, and they'll put it in your office in your building in your region behind your firewall.

You still pay as if it's Cloud. It's Opex model, but you can just operate it within your physical range, and then finally, which may not be relevant. Get one over here, but I have to say this, there's something called alloy. It's dedicated region, but it's not for end user consumption.

If we have a region where we have a partner and who wants to resell Cloud, they can get alloyed, and then they can carve out a small Cloud setup and sell it to multiple desktops. I'm sorry you had a question. Yeah, yeah. So, if you're hosting a cloud.

[Speaker 4]
Do you? Does it scale up the costs and they like increase the hardware? Or is, is it somewhat agnostic towards that? Is this one base cost, and then you just start getting to the software player how we go. The question was, if we are setting up a dedicated region.

Is how the economics work?

[Speaker 1]
Is it like when you're setting of a dedicated Vision, there's a base cost to it, or is it same as positive question, so no, it's the same thing. There is no, like, a down payment or base price kind of a thing. Response.

So, yeah, and then the last thing which I wanted to actually talk about is available in the slide. I'm not sure how many can see, but there's a Microsoft logo over here. It's a Google logo, and there's an AWS server. The reason that thing is over there is. Because multi-Cloud is our identity, Oracle is the first one to set up a connectivity.

We have dedicated connection productized connectivity with us. Here we started with Azure. Then we have connected with Google, and then we have. It is connected in U.S. What it means is is three cloud providers don't talk to each other. You can set up as a customer, you know, but they don't talk to each other.

But Oracle has connectivity with all three of them. So, if you decide that I want to run part A of my business on AWS, I don't want to move it, but I want to use oci for something else. You can do that because we already have the price and everything.

Uh, cohost of services which are available and then something which I already talked about commercial public Cloud government Cloud.

Uh, I just do some of the slides. I'm not sure if I'll be able to leave on time, but I want to give some time to Jeremy, but anyone has any questions okay?

[Speaker 4]
Name is Jeremy Mendez. I am an AI architecture here at Oracle. I'm probably the most boring person you'll ever interact with at work, but when it comes to developing any type of ml or AI solution, I just because I don't build cool stuff. I generally tell my customers, you know, no,

[Speaker 5]
You can't do that, or sorry that's impossible for you. Know there's a much more costly way to do this, but you're not going to want to do so.

[Speaker 8]
Um, today we'll run through some quick slides. I think I have five or six minutes, but we're going to cover oracle's air strategy. What it means for taking Pilots to production, and they want to go through a quick little example of how to how to deploy agents in a certain a certain some of our services.

[Speaker 5]
Okay, so Enterprise AI of generally always breaks at the interfaces. When I say interface and the scale data to interface and the trust interface, and so? You know, agents are are very burstful. So, there's peaks of demand, and they, they reason, you know, in parallel, they need to scale, not just vertically, but also horizontally data interfaces.

Be sure that agents are grounded against trusted structure, say, maybe structured, unstructured data, uh, tool interfaces, making sure that agents are applying to approved tool assets apis,

[Speaker 4]
Sql mCP servers, business actions, and then, most importantly, is the trust interface, right? Because this is security entity system. Providence is human oversight algebraically. All this stuff must be designed up to the very get-go.

[Speaker 2]
Really has to convert the stem around Enterprise agents, and so we start at the bottom at the base of this upside down pyramid. Um, it starts with infrastructure as my colleague talked about, right? So, this could be all GPU compute clusters, networking regions, distributed Cloud, Etc. Then there's the agent runtime, right?

So these are going to be places where we're building models, tooling, memory retrieval systems, all the governance stuff, um, and then above that it's going to be our foundational there, right? And this is probably. Really. The most important piece of it all because where the agents are going to be grounded to actual rules and data.

And there's going to be databases Oracle lake house systems Vector solar systems that create that that data Foundation, um, and then we have the development study, right? So, this is going to be things like Oracle's down platform where you can, you know, build out these agents, a private agent, Factory agent Studio, and then, of course, making your work within your business application layers, Fusion application, or some third-party application, and this is really where we go from the core of building everything.

Actually deploying Prudential. That is so gorgeous. Quickly highlight just a couple places where we can actually build agents quickly on oci. So, the first place I'll touch is really, just, you know, the fusion application. So, if you're a fusion customer, which a lot of people out there are, you can take that.

You can take advantage of the agent Studio, which allows you to basically download Marketplace templates. These are already pre-built agents. You can deploy them for whatever domain you're working on. There's a finance domain, a supply chain. It's basically just, you know, a low code environment for familiar all these days, and the beauty is that you get to build all this directly on your your ground truth and your solar trust disorder systems.

Let above that at runtime, right? This is where the infrastructure comes in a plate, because all these agents, all these l M's all these machine learning models are going to be running on some poor aoci, uh, infrastructure, and this is going to be the GP, GPU compute, or Rema network, you know, hydro storage, uh, deployment choices all that stuff, but then also to the Enterprise AI agents.

And so this is where you can build agents directly on top of OCI or whatever scale of

[Speaker 4]
Use. Whatever response API you use conversational memory containerism, you know?

[Speaker 2]
And generalization. Everything you need to actually deploy your age and debt skill level.

So missing the header here. But this is basically that foundational data plane layer. So this is going to be a lake house on oci, it's going to be AI lake house plus oracle's data platform, and the beauty here is that we're really going from wrong to AI radio data with live zero copy systems.

So, the following our medallion architecture, um, building systems around open plus Oracle engines, uh, and then building, setting off these a to a protocols so that we can design the agents inside oci. Talk to other oci systems or expos. Outside University, I talked to Downstream applications. And then directly inside the database are tools like select AI, where you can basically build local environments for building L2 SQL Solutions rag Solutions.

Again, these can be exposed outside. The database can work with data sources from outside the data database, and this is really as close as you get the grounding against data, because your ability, an AI agent directly on top of your data system.

[Speaker 4]
And this is the AI data platform. I'm going to play this video, um, because we're not because I put a pressure time. It's going to go real fast, but this is a data platform designed for the engineering tests and machine learning tasks, Alliance tasks, building out agents, and in this workflow, you're basically triggering your process with some chat trigger, uh, playing guard rules like single buyer agents of applying execution agents, uh, calling out your tools, and then ah is supported here as well.

So whenever you do have a system that does support or? Hey, you can explore the Asian card directly to that system, and all these two agents are talking with each other again. This video is going really fast, so if you want to talk afterwards, I can show you a slower version of this.

And other places are low code, private agent Factory. Now, this is gonna sit near or adjacent to the database system and does support connecting the third-party source. So, this is going to be true to no code.

[Speaker 6]
So, it's very node-driven. It's very UI based. You can plug in a wide range of different tools, including select AI tools, which are built inside the database instead of your own mCP servers and call those tools where mCP server you can set up your API tools, a wide range of angles, and once you deploy here, you can basically hook it up to any Downstream application, uh, to host your product area.

And I wouldn't do my dude Villages if I didn't talk about what an actual deployment looks like on oci. Now, this seems rather complicated, and it is because it's just three agents that use it for customers using their EBS staff. It's sort of a challenge in Enterprises. Is that, for example, EBS doesn't allow you just to hold data out?

There's an underlying database. There's an actor you can take against the UPS system driven API. You have to replicate data you can't replicate data into production database, and they can do there, so you need to create a separate database system to deploy

[Speaker 9]
Your vulture storage. Everything you need out of MW SQL

[Speaker 6]
Tests? You need multiple compute instances to scale vertically or horizontally containerized across oci. So, for a single use case like, this becomes a much larger from. Basically just deploying an endpoint. And so, to sum it all up right scale context workflow. And having a family to build agency is generally how we go from building Pilots and moving them into production.

Thank you! Sorry, that was nice.

[Speaker 4]
Thank you very much to the other question.

[Speaker 1]
For, uh, Enterprise organizations looking to potentially use it. Do you guys have any starter programs or transition programs anything like that?

[Speaker 6]
One of the startup programs, which existed for a while back. What I left look on the map. We have a ton of enablement programs. Anybody is familiar with AWS, your gcp. We have specific trainings for AWS architects from YMC I. From a credit standpoint, everybody could go on oci right now.

Sign up for a free tier. We get 500 of free on my credits immediately.

[Speaker 7]
Enterprise standpoint. Contact me or where is Andrew? So, this is good for me. Yeah, yes, I'm Luploma. I'm a sales manager here at Oracle. I cover our strategic consults group Jacob's right here as well, too.

[Speaker 5]
Dj's over there. One of our leaders, he runs our entire Ace team, so anybody who's ever interested and Michael Shields too. Sorry, there's a lot of people Oracle people that I don't know.

[Speaker 10]
But contact your sales rep. We definitely have a ton of different programs to get you guys started on oci, and the promise is once you guys try it. I guarantee you that you will stay. I think our friend said, hey, I don't know. We'll, uh.

Thank you Oracle team!

[Speaker 2]
For a presentation. As a data look. Can everybody?

[Speaker 10]
All good. Okay, hi, I'm done. I'm a software engineer on our agent of observability team at datadog, and today I'll be talking about developing agent evaluations that matter. A little more context about me. I'll let it work. I do also do research in AI, title, impact, and evaluation. Um, that's going to color kind of how I talk about this.

My work's been published under its HTML. Um, just a Vibe check before we like, get into the talk. How many of y'all have worked with coding agents? Close everyone. Also, who's built in Egypt?

[Speaker 1]
Great. Love that. Okay, if there's ever a time I use any terminology you don't know, please ask for him.

Anyway. So, how do we trust AI agents and systems?

[Speaker 10]
Yeah, agents and systems are not deterministic. They're built off of a generative AI models that are these billions of perimeter large models and do not behave from the deterministically. This makes testing them a little bit more challenging than we do. When we write traditional software where things behave a little bit more additionistically, and we can be more.

With unit tests, we can have greater coverage. Obviously, end-to-end testing is still necessary, but testing is a little bit easier. With agents and systems. We have this non-determinism. Allows for lots of cool things, but also me testing a little challenging.

[Speaker 1]
We really need to

[Speaker 10]
Understand AI agent performance prior to deployment, as well as what failure remote. What are failure remotes of the agent reported, and what are its limitations? Obviously, with this non-determiniscent, something bad could happen if you haven't even acting not in a manner that you intend for it to. Potentially, it might delete something that's really important if it has proper permissions with tool calls.

And we really would rather not have that happen. And then benchmarks have lots of limitation. Benchmarks are used to evaluate performance of models, but don't necessarily cover how. Agents and AI systems are being used in the real world, unless have limitations in being able to tell us like, how actually is my agent or system or whatever going to perform when I actually deploy?

Similarly, we read TV and can be quite time consuming. I may not provide sufficient coverage for a little more. The more context about what grunting mean is typically Frontier companies that are building these large models. So, OA anthropic, while renting their model and tests a lot of variety of different, um, tasks to try and understand.

What are the? It's a bound like what the model can do, particularly for safety, but if you're developing an agent Care system, you might not have the bandwidth to do this, and you might not actually cover how your users end up using the model, and your users might end up using the system in a manner that you didn't even consider.

So, why evaluate AI systems? Emily reasons are in part how we build trust in our AI agents and systems. Evaluation does not measure something meaningful to agent performance. Um, can help us trust that our agents and systems are going to behave as we intend them to. So, how can we develop meaningful evaluations?

We need to understand first what we seek to measure in our evaluation. This is super important. We need to like, actually know what we want to measure otherwise. Building an evaluation without this context, like, is it going to? Be meaningful. We also need to have a plan for how we're going to measure this and have an idea of what signals are going to give us insights into what it is easy to measure.

So, how can we develop meaningful evaluation? What the f*** responsible AI literature, um, the community has come up with some Frameworks and ways of thinking about this. Some really cool work from Microsoft has come up with this framework, where we systematize a particular concept, and then we operationalize. This concept with a particular

[Speaker 5]
Measurement instrument, and we're able to apply and develop.

[Speaker 10]
An evaluation may be like as a hell of an elevator or some other evaluation topology. Did he kind of take you through? An example I'm going to? Have us, imagine we're developing an evaluation, a recruiting agent where? With, and we want the coding agent and you're interaction with the coding agent, um.

You want your bowl to be completely right? You're like going to your agents? And asking it to do some coding tasks. You don't want to go back and forth with it. You wanted to actually do your your, um, your goal, so this goal completeness. Evaluation that we seek to.

Fix to develop, um, seems quite simple at first, like, bold completeness. That seems simplistic, but in fact, there's a lot of ways in which we can systematize this or describe this bull. Completeness could mean that the agent eventually figures out, um, the users will unleash users full, but there's a lot of back and forth like 10 plus interactions between the Egypt and the user.

That's probably not great. That's actually probably not what you want to happen. Likely what you mean by goal completeness is you want the agent to develop or write the code that the user specified without any of with minimal back and forth. Celebration, systematizing this. Um, we're describing exactly what it is we mean with with gold computers.

So, maybe in our case, we actually are cool. If the hn user go back a little bit back and forth so that the user can clarify what they need, but once the agent starts developing code, we don't want any locking board. So, once we once we've systematize and explain what our evaluation um should do, we then need to operationalize.

So, we're going to need signals to be able to play with confidence. That was, like, bold completeness, has occurred. So, in our case, maybe this means, once code has been written, we want to have a minimal interactions between the user and the system, um, on that same topic. If there's a lot of interactions, it's likely signal that.

In fact, users will. You can also tailor this to your use case. Like, maybe you're okay couple, but like a lot of interactions like, isn't, isn't going to fly. Um, or whatever, it's your building. And then. From there, once we citizen ties an upright slice, so they have that signal to know what is, Will completeness, or whatever it is your accomplishment.

And you know what that concept is? We can then develop an evaluation with that measurement instrument as well as the window concept. So, how can AI assist us in developing evaluations that measure something meaningful? Well, it's really important that when we're building evaluations, we don't necessarily offload the entire process to AI.

Um, and the reason being is, we need to be measuring something that's giving you that we know is important for our project. And so, if you've offloaded all of that. Thinking through an area, how can you have trusted your evaluation is doing? Um, what it's supposed to do, but that doesn't mean I can't be useful.

It definitely can be. It can assist us in Discovery, helping us understand what it is we care about our area and generous as well. To provide to continue with our goal completeness. Example with our coding agent at first spin, School completeness might seem like, oh, that's simple, but as we start asking questions, we're then able to drill down what it actually means, um.

But globally. This means for our context and AI systems can help us in this task of like drilling down to what it is we actually care about. A way in which this can be done is we have the AI system meaning to find what goal complaintances and then the user is then able to fine-tune and modify that until they've drilled down to what it actually means for that.

Okay, assistant can also help us with understanding when you have agent or system in production. There's so much data on on how users are using your product, and so it might be quite might be challenging for an individual or a team to go through all the data and understand.

How is my system actually being used by production? AI systems can obviously help them help with this and help us identify patterns of usage that can then inform our evaluation to politics.

[Speaker 1]
And they

[Speaker 10]
Can also provide a starting point. They can create an initial evaluation that AI Engineers or other folks can then build off of because sometimes like building an evaluation. Fighting little daunting at first, but having something to build off of can really, really help with this. So, how are we doing this at kid about.

Well, we've recently released a feature called AI assistant female creations in Asian observability, and I'm going to take you through a little demo of this. So, sticking with our little gold completeness eval? Um, let's say I want a full completeness evaluation. Bear with me sometimes.

[Speaker 1]
Okay, I'm

[Speaker 10]
Gonna save what I'm gonna write, and I'm going to type the two hands because I'm unhanded. I'm not that good at that. Okay, anyways, I'm gonna write it a goal complete. We want a goal completeness evaluation. That, uh, says that you, the user's goal is completed if there's fewer than two turns between the user and the agent, um.

To identify the task or to do their whatever whatever that they request between five and ten. We'll consider that like, or like under 10, we'll consider partially complete and everything else. We'll consider that the user has their their goal.

[Speaker 1]
Now, it's thinking.

[Speaker 10]
Okay, also, and oh, you should just like, right here. And so, we see it's explaining some of this, maybe. In fact, I decide, oh, I completed under two turns, like, not obsessed, but how this format is, but that's okay, we can. We can then modify, and then we have some structured outbreak here.

Like used as the signal to understand whether goal completeness in general evaluation development. I was strongly strongly recommend using software alphabet as to kind of ingrain these these signals and then be super concrete and like, what each of these, um, descriptors are, and like how it is? So, in addition to this AI assistant email creation, we also have another feature.

[Speaker 1]
Has

[Speaker 10]
Almost yeared or wait. Maybe it has yay. We move really fast, like, lots of things are are deployed anyway. We have the center called Paddock, and so what patterns does is it finds patterns in your in your um? In their usage products. And so, as I was, uh, describing like this understandability, like, understanding how your AI system is being used, your agents being used patterns can really help.

Keep like, here we see finance request handling. Likely, we might want to have an evaluation of that covers. This maybe has something to do with finance to ensure that our engine is performing as being intended to go. So, what's next for AI assisted demuncation? So something we're building. And we'll hopefully be really soon.

Is that back and forth that I was talking about? So having, um, the assistant. When we're developing this evaluation, ask the user questions so that the users send people to more concretely describe what it is that they want to evaluate, because oftentimes we, like, at first. You can't succinctly really vocal business.

It seems like it makes sense, but then, as people ask questions and you're able to really understand, oh, it's actually. This is what I'm looking for. So, some key takeaways from my talk here is be clear about what your evaluation measures. The evaluations you develop should measure something that matters to you in this space in which you work in.

It is relevant for your AI agender system. Use meaningful signals on your analyations. This is quite important if we're if the signals by which we're using to make. Is it just an, or consider whatever score it is or not, meaningful or not related, or don't correlate with what it is we seek to evaluate, then the evaluation is then very helpful, so it's super super important that the means by which that.

You're determining your evaluation outcome, are meaningful, and measure something that matter and are related to what it is you're seeking to measure. And number three. Obviously, like, evaluate your agents super important to understand the performance and limitations of your agents and systems before shifting, shipping to production, and to continue evaluating your agency, even when their introduction as the way that users May interact with them, might not be as independent to be.

Um, and it's kind of cool to continue developing evaluations even after, um, agents and applications have been deployed that then covered the these usages that you're likely to discover when people actually use the things you build, uh. Anyways, thank you so much for listening. Feel free to ask all questions.

Hope this is interesting.

[Speaker 1]
That's a simple question. Oh no, there is okay.

Yeah.

[Speaker 2]
Yeah, we support. Okay, okay.

[Speaker 1]
Thank you! Do you guys support like, uh, clients harnesses like people's clients and all this stuff? Yeah, it's for HIPAA consignment. I mean, is it like prepaid or?

[Speaker 4]
You know, I'm I'm seeing, like a lot of companies watching out to at that layer of information, like you would use agent observability to have your hip hop compliance. We don't offer a product for that, but if your agent is already HIPAA compliant and you trace an observed via agent observability like you're a student?

Okay, but you want to like, create that evaluation with yourself as much.

[Speaker 10]
Well, like when you're using, like, whatever models that is that you're using. Like, let's say you're using opening opening manager or whatever, so you kind of a product or something. Lately, the model that you're using if you need to be HIPAA compliant is hypo compliant. And, like, I guess, like, the date of protection, part of your user's data.

You would need to do one more, but the act of using R evaluations to. Like, test your mom, your age of functionality would would be.

[Speaker 1]
Um,

[Speaker 3]
When you're using an llm Community evaluation,

[Speaker 2]
Help. Have you found that certain models are of good at doing that helper role of doing the event, helping design the evaluation like you should on the screen. Or is it? It depends on your data use case and earlier. It's about the context you feeder.

[Speaker 1]
I

[Speaker 10]
Think it's been a matter along, but the contents you feed it, I think. Also, with what I showed, we have some requirements and that we need things to be fast. So I think latency was a big factor and what we in the model we decided to utilize, but I think context is going to be super important.

Because, like, if you have like a poor quality prompt, even a very powerful model, and that was sufficient complex, is likely to not yields and evaluation it's abuse. So,

[Speaker 2]
I'm curious, what was that in your demonstration? Do you remember it was Osama or something quick? I didn't mean to look at the code.

[Speaker 10]
Okay, thank you very much.

So, like if you're interested?

[Speaker 1]
Thank you! So let's have a question.

Cool, can everyone I mean?

[Speaker 10]
Um, hello, everyone. I ayush, I am one of the co-founders of, uh, upcoming called blacksmith. My pitch for blacksmith is very simple. We build the fastest infrastructure for the active code validation. Um, and when I say code validation? Um, typically referring to CI infrastructure. So, everything from compute storage?

Um, all of the caching Primitives that you need to test and deploy your code really fast. Um, but that's not what today's talk is about. To go back to the first slide. Today's talk is, uh. About the? And the Tailwinds that we saw on our business because of Claude Opus 4.5.

Which released in December 2025?

Let's tee this up a bit. You know, over the course of the last few years, we've. We've seen software engineering kind of get.

[Speaker 1]
You know, the act

[Speaker 10]
Of programming and software engineering get more and more automated, um, at these various inflection points. So in, you know, mid 2023, you had co-pilot time completion cursor? Um, it was a people called super Maven, which then first required for really fast pack completion. Towards the of the mid 2024 Mark.

Uh, entropic, large solid 3.5, which was the first model that had, you know, real programming capability.

[Speaker 1]
And that suddenly unlocked use cases like multi-file edits.

[Speaker 10]
Right. Um, most people in this room, I presume, remember, persons, composer, launch, where? Suddenly, you could, you know, issue prompts that would go ahead and edit multiple files at the same time. We would make mistakes, but it was still, like, very helpful in terms of just counseling things out.

Then at some point. In early 2025, we saw the launch of thought code. Uh, plot code was. Effectively, the birds of what you would call agentic coding. Um. At that point, the models were still not good enough to, you know, kind of do end to end feature death in the way that they are today, but it was the first kind of glimpse into the future.

Now, we're slowly starting to see, um, the rise of what you would call a cloud agents or background agents. I like to kind of use the term ambient agents just because. Um. And, you know, now, for the first time, we're at a place where these agents can ambiently monitor production signals.

Look at your metrics, look at your logs reason about the code changes alongside these things and. You know, send a draft, hold request, or take sort of corrective action.

So, what does it mean for us? CI is actually kind of the first, um. Layer in your in your sock that? Feels the exhaust of of all the code that that your developers are generating with AI. It's, it's, you know. For us, it means more pull requests more tests.

Um, these coding agents are particularly good at writing tests. Um, they're also particularly effective at iterating a lot faster if you have a high poverty test we. Um, it also means more, you know, runs of your CI pipelines. More Docker builds as teams are deploying faster. Um, it's also more importantly means more iteration and more sort of candidate changes.

[Speaker 1]
So

[Speaker 10]
For contacts, boxbook today is a eight engineer startup. Um. This means that with such a small team. We need to be able to move a lot faster to be able to compete with larger games that, um, you know, offer the same type of infrastructure in leadershaps and sizes. One of the ways we're seeing small teams like ourselves, um, leverage AI is for every you know small idea of wordpivity working with multiple candidate changes via, you know, important designs for front end or architectural kind of diagrams or a bigger architectural changes?

But all of that also just means a lot more load on your CI pipelines.

So, going back to you know the the? Aisles I had in them. It was like before. Opus 4.5's launch in December 2025 was out of the first inflection point where, um, background agents or ambient agents we click. It felt like it was the first, uh, point in the intelligence curve, where all these use cases suddenly became a lot more viable.

[Speaker 1]
The direct sort of impact of that. Um,

[Speaker 10]
At least based on, you know, the data that we have from our customers is the average developer is now. Producing 83 more code compared to the beginning of the year. Um, you know, not more than five months ago.

So, this is a chart of the inflection that we saw after the launch of this new model. You can see that before this, you, you see a bit of a holiday slump right in December? Um, presumably, folks play around with the new model and, and anecdotally, it seems like a lot of the people I know had a bit of an aha moment, uh, at this time, where they finally realized that these agents had gotten really good.

And then you kind of see the the resulting tail when when folks came back to work, um? The, you know, the normalized CI runs per ore just exploded?

Another kind of interesting data point per us was looking at the number of CI jobs initiated by, um, you know, solely by what you would call our agents or background agents. That grew 11x, compared to September of 2025. So this again is is kind of a normalized metric of the number of CI jobs that were, you know, solely initiated by Cloud agents like Devon or cursor cloud or Cloud code map.

Um. The the inflection from almost 4.5 was was very real.

Interestingly, the. You know, the the split here is about what you would expect? Um, I'm guessing most people here have used cursor or still use cursor like most of their code. Um, cursor style agents dominate our, you know, Cloud agent usage? Devon is kind of a close second. Um, but I guess, surprisingly, surprising to me was a plot code on the web hasn't really taken off in the way that you would expect given, you know, the otherwise popularity of the of the product?

[Speaker 3]
By the way, if anyone has any questions if you're stopping and and, um, have to answer.

Another kind of interesting Fitbit, which I think. Baby is intuitive to a lot of people. Is this is a chart of the CI job failure rates over time? For jobs that were initiated by coding agents? So, as you can see back in, you know, September?