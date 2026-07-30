  
This is one of six parties that we are hosting. We have.  
  
\[Speaker 1\]  
New York, which you all sold out amazing. We have two in Estep. Both of those have sold out as well. We have one in Austin, one in Seattle, and then one in London, where, uh DSP, uh, creator of MCP, is there, um, we couldn't get him to come an hour, but he lives there.  
  
That's why, uh, and then, uh, Amsterdam, and the other one. So, lots of momentum. I've seen company blog post lots of. Today about with this unboxed for Enterprise. So amazing, amazing. So we're going to get into, uh, more about the details of the protocol, but a little bit of housekeeping, so we'll have some talk, um.  
  
Of course, you all already did the network, and I didn't have to instruct you to do that. But during the breaks or after, feel free to network meet someone music. No, take pictures. All the background stuff tag us on social evidence. Also, restaurants. If you're looking for those. You see where that gentleman just came through, you were going.  
  
You would go through there for the restroom, um. Of course, you all found the food. Feel free to get more back. There's Refreshments in the fridge help yourselves speech. Shout out to date is all for posting live.  
  
I've also worked in open stores for a long time, and I have not seen a community that's as active and as vibrant as the MCG Community, they have contributors this board, not just go in there sometime, and I just smile. I mean, it's just like busy pieces, dozens of channels and working groups and people are not just working on what exists today, but what could exist tomorrow.  
  
There's a lot of work. Done, and then we have companies like data dolls that are all like, how can we help? What can we do so we didn't have the big or clean and say, hey, we want to do a Meetup in New York, oh, we got you. Come on in, we'll cover the food and everything.  
  
So big, shout out to them. We are so, so thankful, all right. So, let's get into the meat of the matter. Our first talk is from a friend of mine, and uh, former Kylie Alex Hancock. He is. Software engineer at Block in one of the four maintainers of booths, which was actually the first MVP client to hit the market.  
  
It is, uh, open source. It is, it serves as the reference implementation for MTP, and then Tropic was working on. Reference implication of the model. We were in the background working on the client and working very closely with Bentropic on that. We released schools, and then, uh, who's also a part of the authentic AI foundation.  
  
So, once we sped that up, came over here with goose, and we have Alex to Nigel, uh, he is, uh, core maintainer of Goose, but also on the Russ SDK or MCP, so he has the the. Art that show. What if you need to do to actually get ready for this release?  
  
I think you're ready. Alex is the, it's the Russian SDK ready. Yes, it's, that's right, okay. Can I put you on a spot? Well, it's not merged yet. But we're getting it all right. So Alex, come on up, tell us about the new big changes in mCP, y'all, give it up for an app.  
  
Hello, everybody. Hello.  
  
\[Speaker 2\]  
All right. Great intro\! Thank you and\!  
  
\[Speaker 3\]  
Yeah, so tonight, I'm going to talk about the new version of the protocol character. Sure, we get. That would be just yeah. Just, uh, press the button. All right. So tonight, we're going to talk about the new release of MCT, um, I'm going to kind of give an overview be the best I can to give an overview of the big, important new features how you can use them and kind of what it, what it means, and what difference it will make for you.  
  
If you're writing a program that uses MTV. Um, first, uh, and you gave a little bit of this, but a little about me. I'm a software engineer at Bloc. I worked there for a long time. I just crossed the 10-year Mark the other day five blocks. So,  
  
\[Speaker 1\]  
Yeah,  
  
\[Speaker 3\]  
So I know just kind of a cool thing. I could say this week, and then I'm also an mCP maintainer. Specifically, I work on the rust SDK, so if you're making a program in Rust that either does a client or a server? Uh, an STD, client or server. This would be the library that you would use, and I'm also a core maintainer of producer project, which is an open source agentic harness that was one of the first MCT clients.  
  
So, this is a project I've worked on for about two years coming up on two years, and we donated it to the Linux Foundation, uh, last year. All right, so. This version of MTV, the high level framing and the the unifying thing that make all the changes make sense is when you think about mCP transitioning from primarily being a thing that was used locally.  
  
So, when mCP started, it was, you know, probably inside Androphic, but David and Justin worked on it. I was like, you had caught. You had the cloud desktop app, and you had some other programs running on your computer that you wanted the model to be able to reach out to, and it only had standard Idaho only had the ability to be on one.  
  
\[Speaker 2\]  
At  
  
\[Speaker 3\]  
The beginning, they added HTTP, and now that that's matured. More and more of the usage of mCP is going to that remote use case where the client and the server are on different machines. Which means that the protocol, the semantics of the protocol, need to change to make that work better.  
  
And this is, I would say the thing that is motivating almost all of the changes in this new version of the protocol. It's like a recognition of the fact that MCD is a thing that's more done remotely now than where it used to be a thing that was done on a single machine, so that's like the high level framing that that make these changes make sense.  
  
And this is what I'm going to go through today, so statelessness. The transition of mCP to a stateless protocol is a big thing that you've been hearing. I'm going to dig into that talk about what that actually means, what the implications of that are. Um, there's this thing called mrtr multi-round-trip requests.  
  
That's a part of that stateless story that also provide some examples of and talk about what it means for Server authors by authors, Etc. Extensions and extensibility, so this has finally come to NCT. There's finally a way to officially extend mCP with new functionality that's not going to be in the core protocol, but that that, uh, you know, makes sense for certain.  
  
Certain use cases might not make sense for everybody, so it's not a good candidate for them to like. Accept a change into the course fact, but if you have a certain need. Like, if you work in the health care industry, here you work in banking or something like that, and there's a change that would really make sense for your vertical.  
  
This is this. A great place to do it authorization. I'm going to touch on this. There's some improvements in this version of NCT. I'm not going to talk too much about it because there's a more detailed talk later. Um, that's my. That's my excuse for not talking about. It's not that I don't understand it.  
  
And then we're gonna say goodbye to some things, so Roots sampling and logging are all deprecated. In this new version of MCP, and I'm not going to talk about that much. If you use those features, you know what they are, but they're on their way out. So let's, let's pour one out.  
  
The roots are sadly got a point. All right. I love sampling because I'm really sad to see it. Yeah. All right, so say listens. This is the big Marquee, uh? Our key change in this version, and this is a visual that describes for mCP. I think how stateful went and how stateless is now going.  
  
Uh, the one on the right is also how I used to travel before I had kids. The one on the left is a it's wrong. So let's, let's talk about what this looks like in both versions of the protocols, so. Before going back to November of last year, the version that was cut.  
  
Mcd was a staple critical. That meant is that there was state that needed to stick around on the surgery outside of the lifetime of any school request. So there was an initialized. Between those two, the server, and the clients where there would be future requests in that session. And there was a bit of session State, so there was.  
  
Uh, client capability server capabilities that were negotiated at the time the session was created a session ID and that, and, and what version of MCE was being used for the for the connection, and that's all information that the client would count on the server. Remember? After the initialization Stone, so you do this initialize flow and then all the future requests.  
  
In that session, there was some implied state that the client would count on the server hanging onto, and this creates a problem when you have a multi-instance server deployment that sits behind like a very traditional load balancer that if you have a load balancer that that round robins requests between different instances of a server, which you pretty much need to do for any kind of scalable, right, forever?  
  
Scale to it. It creates a giant model. Um, basically, you couldn't know as a client. If, like sending your request to the balancer if it was going to land on the same server. No, they're not, and so people had to work around this for for high scalability in a couple different ways.  
  
You either had to pin the, uh, like what back-end instance the requests from the client would go to every time you send a future request in a session? Which causes problems where, like, you want to be able to cycle that Fleet out right. When you do something like a deployment, so you want to be able to get rid of nodes and bring new nodes in flexibly.  
  
And that's really hard if you have to have like a session that's ongoing, and they last a long time, and it's pinned that creates a problem. You have to build something to make that work or people would start to store this at the shared session. Information is something that all the nodes could access.  
  
But that. That's like an additional architectural component. You have to set up and deploy, and you have to connect everybody to like a redis instance or something like that, and then their scalability concerns with that. So, it just it became very complicated for people to do very normal things that you want to do, like having a load balancer and having multiple instances of a server with this stateful, this stateful protocol, uh, defining this required session, and this this required session scene.  
  
So fast forward to the new world. After this version, every request, what it really means for the protocol to be saved. This is that every request has the information that it needs for the server to handle it included in the request. So now, there is no initialize anymore. There is no session anymore.  
  
Every request just arrives at the server with the information from the clients that the server will need to serve the request. Which means you can do the very normal thing, like putting a load balancer out there, putting you know some Auto scaling pool of servers to handle, you know, high load and any request from the client at any point can just go to any of those nodes now, and it will have enough information in the request itself for the server to be able to service, which is, which is, hopefully, makes deployments a lot so.  
  
Um, part of the stateless story. Is this thing called MRTamer? So I hope your multi-round-trip requests is going to be something to hear a lot about this single board, and it kind of remaps how server to client requests were in the protocol. So, there's certain patterns many of the patterns MCP are client initiates the request and sends it to a server expects a response.  
  
This is the other direction. This is when the server needs something from the clients, and there are some messages like this in mcp elicitation as. Where the server sends the client a message, and it's expecting a response to an client. And that works differently. Now, it has this. We have this thing called mrtr.  
  
So again, I'll do a before and after because I'm going to use solicitation as an example. So, elicitation is where the server needs to collect some information, like from the user. It doesn't want the model to answer a question or whatever it means, like the user of the NCP OS application, means build a form organization, click a checkbox, or confirm something as permission.  
  
Um, and then it's the server is waiting for a response to get that information before it's able to continue doing what it's what it's doing. So the way that's worked before, there'd be a tool call. There would be an elicitation request from the server like, say, instance a of the server back to the client to get that information.  
  
And then it would hold open a stream. So the, there'd be a stream open between the server, the client and server instance. A, um, you know where server sends back a request object to the client client goes to respond in a new message? A new post with a new body, right?  
  
And because an SSC stream is a unidirectional stream, so that's going, things are going from the server to the client for the request. The response comes over as new request, and this is where the problem can kick in, right where, if. Shows the server instance B, then server instance a is sitting there, waiting for a response, and so to make this work to make elicitation work over the HTTP transport.  
  
You'd have to do a lot of really complicated things in this. In this version of the Protocol, so you have to have some kind of. Sticky session pinning, where where the request will always end up at server instance a right, and that has the downsides that I outlined for, or you have to set up some kind of shared storage mechanism for.  
  
Server instance B when it gets the request to update something in shared State and notify server instance a. And that's, like, you're starting to subscribe to some queue or something like that. On server instance, a just to get these messages back, and it's like it's all this architectural complexity that, just like, isn't needed for this problem.  
  
And so, the new world is much simpler, and it involves multiple requests, so they're more requests going on, but the the conceptual model is much simple. So, now, cl. Does a pool hall at some point on the server during that tool call? It needs more information from the user, right?  
  
Server just responds at that point and says, I need more information to handle this request. And then the client can show the user a form or show the user whatever input required is whatever else they need. User will fill in the form client just makes a new request for the same tool call, the same way it did the first time, but with this additional information included in the request, that way when it reaches that point of execution.  
  
The server will realize I already have what I need to pass this point, right? And it can happen again, like you could do multiple of these in a tool call, in which case another round trip would be required, right. But every time. The information is needed from the client back to the server.  
  
The server just responds with a result indicating that, and then this is where multi-round trip to complete something makes sense, right? Like, this one has two because there was one time on the server needed to request more information to the client, and this can now happen as many times as you need it to.  
  
And then, at the end. Once it's gotten all the way through its execution, it'll just return the total result, and you'll get the toolbox all the way at the end. But this is using the. That MCP is now stable, so each request is completely self-contained. There's no stream that hangs open.  
  
There's no request. There's no shared State. There's no need for cash or anything like that. It's just like all the information is needed is in the request themselves. So this is a really nice usage, like the first nice usage of of stateless to power elicitation. I'm going to talk about extensibility so.  
  
Like I mentioned before, it's now possible to extend mCP and. With this new protocol version being cut, mCP apps has landed as the first extension NCP apps is the the feature where, if you've seen this in, like plot, or tapping a key where you can see, like a UI.  
  
You can see the UI from Airbnb, your booking.com, or any of these companies, or like a weather that shows you a visual description of what the weather will be for the next week. Um, it allows you to deliver UI over MCP resources, and this is now officially like the first extension of.  
  
Of MTP. It's been that way for a while, but with the new protocol release, they're kind of codifying it and saying apps is the first extension. And there's another new one that just landed. The work got done more recently for doing tasks, and I think tasks will be a really interesting, uh, and like, powerful thing that people will start to use in it to be a lot.  
  
And so, I'm going to run through it. Um, it looks like a big chart. It looks like there's a lot going on here. The text isn't super clear, but it's not actually that complicated through web tasks enable, so tasks are give you the ability to have tool calls to do something that is asynchronous and potentially a long time.  
  
So, if you have like a database migration where the model would call a tool, and it would kick off a data, so you should. It might take an hour  
  
\[Speaker 2\]  
Or that or take off a workflow that needs to have a human in the loop at some point. It could be like a day before it complet.  
  
\[Speaker 3\]  
Sure, it's over a weekend. It might even be over multiple days, Etc. This is a way for an mCP server to expose something that's not going to return right away, and so it's. It's a really simple, simple against design, but I think very powerful new thing that is just landed as the second extension for its peak.  
  
So, now you can do, you can do things like, have a tool call. That creates it, and you, you advertise that the client has task capability, and then a task is created, and it gives the client a task ID. The client can use that ID to poll and get the status of the task so you can pull it as often as you want to.  
  
You can just say what is like, is this still being worked on? Is this still being worked on and you complete and the server May eventually say? If I need input like I need, I need now, somebody to fill in a form, or I need you to provide the client I need you to provide some information in order for this task to continue.  
  
Um, so you could have like human in the loop on the client side as well. Um, and then there's a few different steps that it can pass through. Like, you can do an update where you provide information from the client side, and then eventually it will reach a status of completed, and it'll return, but that could be like days or even weeks later.  
  
So now it's possible to have an MCT server that exposes something that might take hours or days, which wasn't really impactful before. With Twin Falls like, it's kind of expected that they would just return within a short period of time. And if you wanted to build something like this, you kind of had to go around.  
  
Now, you can do it in as you can, which is really nice. Um authorization. I mentioned there's a lot of good improvements in this, uh, in this version, um, the big one that I can think of, is that? Clients now require an issuer to be present in the authorization metadata.  
  
Um, and if they're going to validate it for now, and then clients are going to start projecting authorization. Media don't contain an issuer and a future version. There's a, there's a bunch of other changes that kind of just make the authorization set up, make more sense, make it smoother.  
  
Um, but again, I'm not going to get into that too much because there's another talk about it. That's going to go into detail at this time a little bit later. And I'm going to leave with. A recommendation for anybody that's building on SUV. I'm an SD pay maintainer, so I'm like, biased, right?  
  
Because I work on one of these projects, but I think that all of the sdks for MCD have gotten really good, and with big changes like this, this was a very big change to the protocol. I, Our Hope, is that the SDKs make it easier for everybody building out there to just like have a lot of it abstracted away, and you can upgrade your program.  
  
That's either a server or client, and it should be hopefully pretty easy. There will be almost certainly breaking changes in associated with the SDK as you upgrade it to this new version of the protocol. But we did our best to make it as easy as we could for people to upgrade their programs.  
  
Whereas if you were writing an MCP program and you were like handling the messages me? Yourself, either on the server or the client side, that you're going to have to do a lot of work to do this upgrade because we had to do a lot of work in the asking phase, right?  
  
But our hope is that it kind of like putting the protocol behind a layer of code that's a bit more stable and where we'd have some more long-term thinking can can make it easier for you to upgrade as MCP exchanging. So if you're writing a program that's not using one of the sbks.  
  
Take a look in your language and see, see what the option would be. They're all pretty good these days. And, like, I said, I work on the Rasta CK. And so Shameless blood for our project. The Russ SDK is now 3.0 where it will be after I emerge in VR.  
  
It has to be today. If we do it today and it's successful, then we have a couple other requirements that we're going to need to meet, but we will soon have the rest SDK in the tier one category, which means that it's like fully up to date everything is supported.  
  
Um, you'll have some guarantees of, like, if you open a bug against the SDK, or you need something triaged, you'll get that within a certain amount of time. We're going to set up a cross-company roster of containers that are going to look out for this project and want to guarantee, you know, we're triaging things effectively.  
  
We're doing bug fixes quickly, and everything will be nice and supported. So also, if you work on press and you want to help with questions. And you can get the SDK of the CR code. That's all I have is.  
  
\[Speaker 4\]  
Hey, thanks a lot. It was pretty really good. I had a couple questions. I apologize again. Just a mistake. So, what are the things that you explained to the user request thing to essentially get around, like the session, say, Club. Is there a question supposed to be exposed in the context of the codes or model is using it, Etc.  
  
So, is that like, purely like being transmitted in my head, also avoided from the context window, and then the other questions that I had was like. I think on the tasks piece you mentioned that from what I can tell from a diagram look like the intent was for tasks to be like updates on tasks to be communicated by appalling.  
  
And I was curious if his final thoughts around using my post just doing the same time.  
  
\[Speaker 2\]  
Yeah,  
  
\[Speaker 3\]  
But it was really good. My book. So, the first one, uh, do you put the tool call like arguments and things like that in the conversation, and wherein the basically in the context, the request, it, yeah, they're they're requesting, um. I mean, it's a little bit up to you as an MCP host.  
  
It will  
  
\[Speaker 2\]  
Winter, right? So,  
  
\[Speaker 3\]  
I, I sit. Like, I'll answer this question, I guess. From my scene working on the news, where goose is more of an agent project that uses mCP as one thing that it does. We put a tool call requests in the conversation, right? So, like the object that we send the model.  
  
Every time there's a new Journey and conversation has the cool call history, the tool call requests and tool call response mirrors, right? You want to be a little bit careful as it starts to grow. So, like, at some point you run out of context, and you need to. You need to compact the conversation down to a summary, but there's usually one more step you can do before you do that, like, big bang, like, I'm gonna summarize everything so that the context window gets small again, and that you can look at the old pairs.  
  
The old pairs of two call requests and tool call responses and slim those down. So, if there's like a huge response, right where read a file. And then there's like the whole what? Whatever, like a giant Json, like a text document or something like that. In the response, you can like.  
  
Do things like shunt that out to a file, and you can replace the result with, like, okay, model, if you need to know what this full result was. You can read it at this file path. And you'd, so you can. You can modify that state over time, as it makes sense to try to make the best use of s\*\*\*.  
  
You can of your hunting school, right? Um, and then the second one was about tasks, so polling. Yeah, as far as I know, the polling is the is the way that this extension is currently working separately from tasks. There is something there's a working group activity that triggers an events behavior that is thinking about this.  
  
That is thinking about how to do things that, like, trigger. A real-time identification bio weapon. There's a lot of discussion going on right now, so I'm not sure what that working group their latest thinking is around the delivery mechanisms. But what books are a thing that I've heard discussed for having like an mcp server be able to, uh?  
  
Send an orientation to client to, like, wake up and do something. And that's, that's really cool, right? Because you could imagine, like, a web hook that could trigger an agent to, like all of a sudden go, start working on something now. And having, I think mCP offers us potentially a good delivery Channel for those things.  
  
So, if you're interested in that, join the Discord and plug into the triggers and events. We're here.  
  
\[Speaker 5\]  
I told y'all that they'd be working and those little working groups in the Discord cooking.  
  
\[Speaker 1\]  
All right, anybody else? Have a question? All right. I'm here and in the back.  
  
\[Speaker 5\]  
How long will it take for the major clients like clock.ai judgment, incentive experience, Gateway greater,  
  
\[Speaker 2\]  
Yeah? So, uh, the question was, how long will it take to major client if the mentors to respect everything respect?  
  
\[Speaker 3\]  
Uh, I don't know. I can't speak for open AI after I'll pick. I don't care about those companies, but um. On Goose. I can tell you if you swear we're at so goose is an MCP client, and we've done all the work now in the rust SDK to support everything like at the library level.  
  
We have not yet told the new versions of the library into goose, outdated everything, so that when you're using new, simple work with a new stateless server. But I hope that that, like we, we will basically get the consumer experience right of, like somebody who is pulling into this library and stuff.  
  
They and My Hope fingers crossed is that it's not like terribly hard for us to do that, and we can do it in the next week or two, at least reviews. I can't speak for the prophetics and stuff, but but I will say, codex, and, uh, co-pilot, are now both using the rust SDK.  
  
So, the like, there's a number of products that are coalescing onto the singing, the the. Days, and so they'll all move like the library will move at at the pace of the spec, and then client implementers will just continue measurable.  
  
\[Speaker 1\]  
I did see Clyde put out a black post they made. I didn't break it, but they may have some news about their 7 280, right. Hey, there's no, yeah.  
  
\[Speaker 2\]  
Whatever is your server using it? What operating system are you using?  
  
\[Speaker 5\]  
For, uh,  
  
\[Speaker 3\]  
The question is what operating system you're using to run a server  
  
\[Speaker 2\]  
Can be any?  
  
\[Speaker 3\]  
So any, any, um, operating system that you can run an HTTP based server on? Will work fine friends.  
  
\[Speaker 2\]  
Hey, I  
  
\[Speaker 4\]  
Just had a question about use case. So, with obviously improvements here, it makes it a bit.  
  
\[Speaker 3\]  
Can you say hello, can you put a little closer to her? Was that? Yeah, that's right. Here we  
  
\[Speaker 4\]  
Go, um, obviously. Uh, the implementation here makes it easier for anyone to, uh? Went long, right, past, pulling as far as tests in the blue. Uh, was it multi-term request? What are the use cases that you think are most interesting that are told up to the surface right now.  
  
\[Speaker 3\]  
Yeah, it's a good question. Um, what are the potential use cases to be honest? Like, we have to just see what happens in the community and, and like, I'll be really interested to see what people do with these new Primitives. I think the mrtr is just like the multi-round trip of Mustang is, just like, strictly a better way of doing that.  
  
It's strictly a better way of doing requests that need to go from the server to the client and get a response. It, it's just a better design. It's just simpler. It's like, easier to use, and so anything that needs to do that. Any new protoc? Features that are sort of like elicitation.  
  
We'll use that same pattern, I'm sure it'll just be a lot smoother. The task one is where I don't. There's so many things I can think of, like, like the examples I gave of. Processes where there needs to be a person. Of tasks.  
  
Asks, and I think it's, it's a really nice use of the new extension system, and we'll, I'm sure we'll see a lot of things emerge in MCP that weren't possible to hold, because so it just didn't have support to people anything at that time.  
  
Hi, can you hear me different?  
  
\[Speaker 2\]  
Um, I'm just curious. Do you go back to the diagram that shows the multi-turn must? When I looked at it first, my media.  
  
\[Speaker 4\]  
Thought, was this looks very similar to the next World? Two-stander, which is machine being? I'm just curious. Was it inspired by it, or did you buy any chance to independent? They arrived to that conclusion  
  
\[Speaker 3\]  
That just a better way to do that. That is a fantastic observation. I agree. It is very similar to x42. I swear to being the payments micro payments kind of protocol where you can request a resource you get blocked, and it says there's payment require. And then you have to redo those request with payment proven in order to get the resource set.  
  
I agree, they're very similar shapes. I'm not actually sure who, like, I did not do this at work. All these ideas that I'm presenting are are things that came from community members, other maintainers, core maintainers of mCP, so I didn't necessarily deny these things, but I'm not sure how that how their thinking was inspired.  
  
But, but the cool thing is, if you find so, this is, like, uh, Seth, there's a little identifier there accept 2322. Um, stands for specification enhancement proposal, and you can go see all the steps on the MCP website over in a given version, and then you can go to the GitHub issue where they were originally.  
  
Now, they're PRS, but you'll be able to help VR and see who author did it. See the discussion that happened on it and and then just reach out to that person. Um, I would. I was very interested to know. Yeah,  
  
\[Speaker 1\]  
This drama work. That's true. Report  
  
\[Speaker 2\]  
Back  
  
\[Speaker 1\]  
To class, but some of the companies that worked on a school, too, are also very involved with the hcp. So, it could, it could be an overlapping all right. Thank you so much, Alex. That was wonderful.  
  
Okay, great\! All right, so? That was great. Alice gave us an overview of some of the biggest changes in, uh, the protocol, uh, we still have more lessons to learn. For those who are standing, y'all go back to the standing room on. Okay, if you're sitting and you have an empty chair next to you.  
  
Raise your hand for those who are, oh, look at on, but those who are standing. If you want to find a seat, we have locks. All right. Front row is completely empty front row completely. All right. So, next up, we are going to have Scott, yeah, who is a senior software engineer at datadog and he's going to talk about ongoing lessons that he's learned from operating the datadol mCP service.  
  
Welcome Scott.  
  
\[Speaker 2\]  
Let's see\! Hello, hi, hi\! Good evening, everyone\! Welcome to data talk.  
  
\[Speaker 5\]  
So, uh, my name is Scott. I'm a software engineer at the Ada. I work on the mCP server. So, first, what is Theta dog? So, in a nutshell, you send us metrics, traces, errors, and so on. Observability data about your service? And we provided tools to help you figure out whether our service running is expected.  
  
Whether there's the outage and why? And how do you fix it?  
  
\[Speaker 4\]  
So, we have a nice website. You can check the metrics of the service to see if it's healthy. And we have a bunch of tools to visualize how it's running. So, you have lots of data that is inside there or not. What can you do with it? The study, but there's a learning curve.  
  
So, for example, just to search Lots, there's a syntax that you have to learn. And if you want to, you know? Matrix, you have to learn another syntax as well. Today, you can just ask your agent because of the SCP server. So, here is the demo of how we can use the M3 server connector to call code to help you get some cost optimization recommendations without needing to learn how to use data at all.  
  
So, here we can ask, like, how can you find all the hosts there under utilized by some definition are utilized? And give some cost optimization recommendations.  
  
And this all natural language, so you don't actually need to know any, uh, next.  
  
As you can see, it changed a bunch of two calls. To figure out what it needs to do. And then it gives you some of my thumb recommendations close him.  
  
\[Speaker 2\]  
Now then, now they have your, uh, your insights. You can then share the inside outside the agent section by creating a notebook.  
  
\[Speaker 4\]  
You're inside the the MTV server. There is a tool that can let you create a notebook inside your doc, and from here, you can see that you can go to the website and share this link with your teammates. You can see all the recommendations that they have.  
  
So, what I want to share here is that with this MTV server, you can unlock new agenda access patterns. But what we found is that as we operate this mCP server, we find that they don't really scale. Well, organizationally, and I'll explain why. And we have figured out that we can use the distributor arms to be architecture.  
  
It will help our team get out of the way from the two from people who are expanding the tools. So, I want to share how people are using the MCP server. So, we find that Ivan mostly using it for diagnosing errors. So, more than 50 of our users use it of a sessions are for diagnosing errors.  
  
And then there's a long tail of use cases such as reporting. Instrumentation improvements. And for change tracking and ever change management. But one thing that I want him to take away from it is that all kinds of ways that you can use a lot through an entity server, but you don't need to be an expert to do any of these things, because by just connecting your favorite coding agent.  
  
Through the MTTP server, you can just use natural language to do all these things. And inside. There we are using the MCB server to do other things as well. So, as floating agents that models have gotten better, we are generating the daily reports from a server lost analyze Trends and to post on our team slack.  
  
So, this allows us to see what's going on, uh, inside our MCB server itself, so we can use Siri server to help us debug on TV server. And we also do a daily part 3. So, for example, we have, we can give a bids code also. Uh of our products.  
  
To look at the last 24 hours of loss to see what is the most recent error identify its root cost? Implement the fix and add a test to reproduce the origin error. So for me, I have it running in the background on a daily, and so I can have a PR to review and see.  
  
It is actually to see whether they can fix the code or fix any errors and without me having to actually write it for myself. So? We have external facing agents that counted it. So, for example, we have this investigation that uses the MTV server for two calls. And we also have Biz chat, uh, chatbot, that allows you to talk to the data book through the data log website.  
  
Internally. We also use it to help our. Help me just because now, there's a console idea to the base for multiple agents. So, for example? Before. Uh, we had well. This investigation was. Had his own tool connection before mCP existed. So, now you can just connect to an off-the-shelf MTV client without having to compend their own.  
  
Okay, and now we have multiple agents, and so we just need to connect. You can just use an off the shelf image behind and connect to the same tools. And often multiple multiple Asian teams. They find that they have to. Optimize the tools in the same way. For example, total efficiency best practices like pagination.  
  
And we also want to have a constant tool service. For example, we find that we have multiple API Services that implement the from N2, tiny duration, like from times and two times in different ways. Some of them they have the user. We use natural language like relative timestamps like, now minus one hour, and some of them only accept Unix timestamps in milliseconds.  
  
There are also some tools that that only take, for example, an array of sort Keys. Allow us to take almost separated values or store Keys with, like, minus time, to flip the sword order. So, if we can have a consistent tools are based of all the different apis that you have.  
  
That makes it easier for the agents to make the tool cost correctly. And we also find that one thing that is quite challenging for multiple agents is to plug them 11 context to the query servers. So, for example, we often find that if you want to write and to make an email.  
  
It, and as reproducible, you want to swap out the data, such that when you rerun the data. Is actually the two calls are returning the data as the data is the same. But when you want to? For  
  
\[Speaker 3\]  
A different session.  
  
\[Speaker 4\]  
Or different house scenario. You want to pass in some color without config to make it a return different kinds of data. Now, um, every single agent used to have to invent this once, but now then, three star. We can just do this logic for them, and they don't have to think about this again.  
  
And it's not just for two calls that Asian. There are Asian teams, one consolidation. Now, they also want to consolidate skills so that all the agents can benefit from the skills that people are finding out. Ways to combine how tools can be used together. And we also have mCB apps that serve to produce.  
  
I have visualizations. So, here we have a way to show using just. Just to get a lot to to find a user panel from app to checkout over the last week. And here we have the interactive widget that can be displayed on our desktop. And this is mCP apps.  
  
One of the extensions I will mention. And we had a citizen growth in traffic over the last five months without our toll costs have increased more than 10 times. But, what's interesting here is that the number of initials calls that are actually more than the number of two calls, which is quite inefficient.  
  
If you think about it, right, like the whole point that CP server is to allow tool calls. So, why do you have so many initialized calls? So, what we find is that when, because a lot of our Ides are this PCP host, they connect to the to some mCP servers.  
  
By default, they adopt me one of them, and when people open their laptops, it just makes an initialize call without ever making a full call you. They need to build media, so this actually a source of inefficiency that we hope that this new spec will help us optimize. And I haven't been scaling so far to handle this growth in traffic.  
  
So far, we've just been using a Bollywood and session store. And when we need more? But he doesn't have more replicas, and this is working so far. Uh, another thing that we have to do is during anything. Sometimes, when there's an investigation, there's a huge burst in traffic or before we have the park.  
  
Before we had. The authorities for that Matrix away. People will just get Matrix one by one, and it caused a huge spike in traffic. But now, also, we have to put in some very different things so that, you know, we don't think it doesn't kill us around. But another way that, um, the scaling happens, is the number of Integrations.  
  
And open the same period of time. The number of tools I've brought from 47 to 197, and it's going to grow even more because our LCB so red doesn't actually prevent all the apis that are publicly available. So, it's going to grow even more. And the number of products, which is roughly tracks to the number of tool sets that we offer, has grown to about maybe three, so you can imagine, uh, this being a source of pain, and I will explain further.  
  
So today, the MCU server is a single binary that contains all the tool descriptions and implementations, which means that we are the color owners effectively for this or every single tool description that goes in. Okay, so every time while on this 83 teams want to change the tool description, or they want to split this code into, or add one new tool that they haven't invented.  
  
So, we have to review the code and becomes the ball left, and you might ask, why don't you just let them submit the code without, you know? And why do we have the colonist? The problem is that there are that the each tool can actually affect all other users, right?  
  
Because The context is a shared resources like shared Commons. So, if one tool is very inefficient with? With tokens in the full description, it will affect everyone else when the iron does these tools. So, and we are indirectly responsible for the user. Experience for all these tools, and so that that adds to alsoever responsibility.  
  
Like, when we review the code, we have to check okay. Well, they said when they declared as hypo comply. Is it actually hypo complied? We have to, like, actually look into it. Uh, one other thing is that, uh, by being on the MC server team? I, I feel this very strongly if we get paid when two failures and see there's a new threshold.  
  
And so, imagine, with 200 something tools of what kind of experience that it's like. Besides just operating the service, we also get complaints about unexpected food behavior for some Niche products so. We can't possibly know all the all the use cases for every single product, and so we then went to group it down call.  
  
When people ask us and by us being in the middle, we actually slow down the. Where to slow down, how quickly they can answer the question? Yeah, and um, you still, we're still going to have more tools all the time. So, to solve to solve this problem, we are going to migrate to a distributors system.  
  
So, the idea is that? The individual product teams are going to own their own MTV server. Mtp server, the electricity, or the Matrix MCP server, and so the two costs will go directly to the logs MTV server, but without actually exposing a separate URL, so you just talk to minerals MCP URL as if it is as if it is just a single MC server.  
  
By traveling, they are going to be operated by different teams, so we don't have to be. That doesn't need you. One team that's more for the or every single tool. Uh, but today we still we actually do need to pass the the payload because today, to know which tool you're calling.  
  
You actually is actually inside the Json RPC payload, so but we do hope that in the future, this will no longer be needed. Because of this, this guy, so it's going to be like should be headers. Uh, so what do you do in Tools list? So naively, you might think that each of these times three servers can can host on post list, but the problem is that when you connect to this URL, you are going to only get the tools list for each of.  
  
Silver. So, what we do is that whenever someone employs each of this MCA Services, there's a deployed time complete push so that all the tool descriptions and two parameters for volume two subscore and we have two complex servers that serves the tools list. Uh, and of course, we do need a special stock because there's some initialized we still have.  
  
But in the new stainless Tech, we will. We will have global detail, the session store, and we should have entertainment equation. So as MCB matures. While we believe that every MTV server will face similar problems. And so especially there about a small teams create SP. Microservices who are going to need to console this cost at concerns at all there.  
  
And all these issues, like, oh, great limiting or something important that you want to handle in one place and not have every single team can have to think about that. Um, and because every tool change can break the overall experience. We need to think of the context we learn as shared Commons.  
  
Now. So, initially, because we have a single team that is co-owners for all the transcriptions, we start off with just five checker or the, we have the engineer who is reviewing the PRS to see it made sense. Now, we start to have this levels that are created by our own team.  
  
But as the number of products grow, we cannot be the ones who are creating the emails for all the tools. So, we want people we need to figure out how to scale up without ordering as well. And so we do hope that eventually, uh, you'll we think about running MCU server.  
  
Just like the way we think about running an HTTP server, right? It becomes boring technology. It becomes something that an engineer just needs to know, other than being something that is your full time job. So, um, yeah. So, we hope interview with our series of real newspap. We're looking forward to the standard-based routing to clean up our distributed MCP information, more FCB extension setup.  
  
We are a huge fan of the mCP apps extension. We are very interested in. In the skills of FCP sap. Yeah, yeah, and these are going to be new SQL extensions that we are really excited about. Well, we just haven't heard about. And as more develop Engineers become involved in building mCP servers.  
  
We believe that there'll be more people who want to be, who are still in shaping other than the RSV works. And you know, we do hope to be able to see extensions in a way that it makes us enjoy it more. So to return. Yeah, uh, MCU server. I lost new engineering SS cameras.  
  
The only thing MC servers don't scale organizationally. And with this new, you should do architecture. We, our team, can get out of the way and let the two teams talk right into our users. Thank you.  
  
In, uh, there are some free credits for, uh, for free share, and also for startups. Any questions?  
  
Anyone? Oh sorry, twin.  
  
\[Speaker 2\]  
Uh, with the maturity we are looking towards.  
  
\[Speaker 4\]  
And so there isn't open. I mean, I'm trying to do something just beyond what photos do. So, is there any of this authorization the boundary for this for the containment environment is in your mind to multi skill environment.  
  
Supposed to do?  
  
\[Speaker 2\]  
Yeah,  
  
\[Speaker 4\]  
So with the. So, with our mCP server, we have, uh, we are supposed to. We exposed some Scopes, so when you log in when you first? All into the TV server, it will ask you to check what, uh, what all Scopes you are allowed, but inside the all or config, you can toggle whether you are allowing mcp, read, or MCB, right?  
  
So, you only want to let your agent use the read only tools. You can set it. You can just give the your agent read-only access instead of the right access.  
  
Anyone else?  
  
\[Speaker 5\]  
There we  
  
\[Speaker 6\]  
Go. Um, fun\! Question is your larger user today, an agent or a human, and when you think that's what will happen. We suspect that there are agents, but? Yeah, we need to, uh, verify. Any other question?  
  
\[Speaker 7\]  
Hear me, oh nice, um, so I wanted to get a sort of like inside look. If you could, um, a lot of times, we let Ada School a lot of work, but it kind of gets Rocky when it comes to observability. Could you talk about any like unique stories or anything interesting you encounter while trying to kind of build that observability layer.  
  
\[Speaker 6\]  
So possibly for?  
  
\[Speaker 4\]  
Or mCP kills. Yeah, so it is the unfortunate thing is that when we are trying to figure out what is going on, let's say, for example, you are using Cloud code, and you're using a data RMC server. I don't actually know the context below that you put in, uh, to call autos.  
  
So when we see a nmc session, all we know is a tool called Sim made. But we don't know the context in which you are giving us the, uh, the tool call request. So, it does make it a bit challenging, ch. To reconstruct what the user is trying to do, and you optimize their response.  
  
So that is a real challenge or absolutability with just obviously the tools. So, what we have relied on so far is to count on our first party agent teams like, for example, for this chat. This investigation to give us feedback when they have the full contacts. Of what is life on the client and what it's like from the server?  
  
Anyway, now. Oh, great. Thank you um\!  
  
\[Speaker 2\]  
Yeah, so I was wondering, uh, how you kind of think about Toby music because you scare like a lot of talks like, like, 100, or something, right?  
  
\[Speaker 7\]  
So, how do you manage token usage, or do you need that to like the agent? Can you put your sorry, uh?  
  
\[Speaker 3\]  
How do you manage token usage, or do you leave it like today, agent, or solve?  
  
\[Speaker 4\]  
So, for almost all our tools, we have this parameter called Max tokens, so the agent can say how many tokens they want, but we are starting to think that perhaps that's actually not necessarily the best idea, because sometimes the agents will last for 50 000 tokens. And then we are just.  
  
Why do you ever 150 or so? Maybe they're just maybe the agent is not using a very good model, and so they're asking for models and then they need, uh. But yeah, they said, for us, serving have for from MCB starter, one of you, when we read a lot of tokens.  
  
So, write a lot tokens. It doesn't actually cost us, uh, anything, but it's just for the llms. It will cost the MC holds whoever is using that course a lot, but we are trying to optimize it for our users, but initially we. The mess. We thought that back stories were right, but it feels like match tokens is probably not enough.  
  
I needed to be more aggressive as an optimizing tokens. Outputs I, I was sorry. I was also thinking like about, like, the code descriptions in itself. Yeah, so for two descriptions. Um, actually, we are finding that, uh, more more and. For example, I think Caracol is using. Tool search.  
  
So, it's becoming less of a concern. But yeah, when we review the PRS, we try to avoid massive tool descriptions, but I think we are not. We're not really aggressively optimizing for those. Thank you.  
  
So, does it matter how long until it was then trying to share something and you also look out in? Let's say I took a tool is create only, but then all right or create only, but then he tries to melt like some of that like that. Or how did you or your ability to work and?  
  
Yeah, we have a timer of 60 seconds, so you'll just show up the timeout. And if, uh, if a agent tries to do an MCP, right? When they only have MCB lead score, you show up as a 403, so it's very easy for us to see when that's happening.  
  
Amazing\! One more. Hey,  
  
\[Speaker 5\]  
Thanks\!  
  
\[Speaker 4\]  
Um, I noticed that you said that you are guys have already adopted an mCP apps, which is pretty cool. What is the client that is supporting that, or are you guys using it to do? I believe there are three different clients. I know, I believe the chargeability, I believe, uh, Cloud desktop.  
  
It's a closet. There's one more, but oh, good. Yes, fail.  
  
\[Speaker 2\]  
Hi, I'm.  
  
\[Speaker 4\]  
What are you guys using MCT apps to to deliver from a UI perspective and that's in their clients? Yeah, for any sort of widgets that you can deliver. So, mostly, for example if you're trying to get say, you know, um? I  
  
\[Speaker 3\]  
Think there is a  
  
\[Speaker 4\]  
Blog post that we that is from research data.nct apps. I think you will find it so they have a nice blog post where they showcase a few different users things.  
  
Amazing\! Thank you all right.  
  
Thank you.  
  
\[Speaker 1\]  
All right, one more talk. How y'all feeling  
  
\[Speaker 6\]  
Good?  
  
\[Speaker 1\]  
Thank y'all so much for raving the blood watch. Um, I actually blew in here just to hang out with y'all tonight, and they that burned my plane and dropped me off. And um? With BWI possible Baltimore. So then I had to find a uber to a train. It was a lot, y'all.  
  
So, um, I'd appreciate you all showing up for me. All right. Last talk, we're going to have, uh, one of our AI young ambassadors, uh, Michael Levin, who's gonna come and talk about mCP and the authorization Gap and nobody is close? Give it up for Michael.  
  
Thank you.  
  
\[Speaker 2\]  
But yeah, to like, share is there because only for.  
  
Technologies  
  
\[Speaker 7\]  
Are, uh, hey, all, right. So, I know, uh, everybody's carved up at the moment, and it's getting kind of late, at least for me. So, trying to make this as interactive as possible, uh, the biggest thing that I wanted to talk about tonight is MCP security as a whole?  
  
\[Speaker 6\]  
I work with a lot of customers day to day one of the Architects on both pre-sales and post sales, so I kind of overlay escalation point, right? If anybody has a question, I'll jump in and regardless of their cycle, whether it's you know Discovery to, we're implementing this thing in production.  
  
Uh, the three biggest things that at least pop up are cost optimization. How we're going to run this thing at scale. Like, what is the optimal ability look like and security always, always something around security? So, again, I'm trying to make this interaction as possible. Is anybody here not working with security in the mcmp space?  
  
\[Speaker 8\]  
Okay, all right, cool. Got a cool hands up all right, awesome. So when we're thinking about security, what is probably the top thing that always comes up? Especially when there's a new spec. There's a new protocol. There's something new out there. Now is a new attack service right, and this into attack service means there's going to be new threats.  
  
We see a lot around like Asian hijacking. You see a lot around prompt injection. We see all these different things, right? But again, a new protocol, a new spec. That means there's going to be a new attack surface that,  
  
\[Speaker 6\]  
Uh, can come up in the Enterprise that can come up with startups that can come up anywhere and everywhere, right, even if it's just  
  
\[Speaker 2\]  
Your own  
  
\[Speaker 8\]  
Personal computer. Uh, so I'm gonna call out if anybody wants to, uh, raise their hand. What is probably the biggest thing I think about when your? Planting security protocols as a whole. If anybody wants to scream out or something, if not, that's okay. All right. So, the biggest thing that I'm always thinking about is from a security perspective.  
  
Risk as?  
  
As you possibly can. So, how can we start to do that with FCP? And the first piece is usually around authentication alterations. This is the biggest thing that I've seen the most right now. MCT security so? As we can see, there are a couple of things that are in this spec for you.  
  
And then there are a couple of things that you have to think about, and some of these things you've already heard right. Rate limiting art rails policies. We heard a lot about elicitation already right, which is, uh, ironically enough, right? My first slide here, when I start getting into it, but there's a couple of different pieces here that you as the engineer or the user of MCP needs to think about yourself.  
  
So, what is this, uh, kind of enforcement, going to look like? I always tell people this way that I think about it is the analogy that I always use. You have a line of communication, right? So you have  
  
\[Speaker 5\]  
An agent, uh, you have a chat bot. You have Pearl something on the left.  
  
\[Speaker 8\]  
And you need to get from point A to point B, and that could be an llm. That could be an mCP server that could be another agent. Okay, so how are you going to get there? What does that line of communication look like 9.999 times out of 10, I would say, uh, to anybody, just series is, raise your hand, scream it out loud, is a Gateway, right?  
  
So you're always going to have some Gateway sitting in the middle, uh. Now that could be some AI Gateway that you're implementing, uh? Working solo as an architect. So, uh, you know, plugging HQ Gateway here because I'm a little bit biased, but it could be anything. It could even be when you're you're in broadlake account, right?  
  
You can set up rate limiting. You can set up guardrails. You can set up specific security pieces for when you're hitting the Gateway, which is just a public instrument, right? You're going from quad on your desktop across the internet, hitting whatever lm, whatever MCP series with. So, whatever that line of communication is in the middle, this is again, in my opinion.  
  
9.99 nine times out of 10, where security is going to be implemented. You're talking off. You're talking guard rails. You're solving rate limiting. You're talking OVO, uh, you're talking oitc based oauth, right? All these different implementations this is usually going to be done at the Gateway, unless it's done out of your aging harness specifically.  
  
Uh, so like, for example, you can set up token exchange media, your agent artist, maybe any law enforce you're using? Okay, so has anybody here implemented elicitation yet? I know we talked about it a little bit already.  
  
\[Speaker 2\]  
Yep, all right, I know,  
  
\[Speaker 6\]  
I know. I thank you for stealing my thunder earlier. I  
  
\[Speaker 3\]  
Appreciate it. So, elicitation is, I would say.  
  
\[Speaker 6\]  
One of the newest methods of security in mcp, I would say, well, everything in MCP is pretty new at this point. But essentially, it's all about mint pools, and I'm going to show this in a little bit. Once I enter into these slides here, but essentially, what it looks like is, let's say, I have an agent, and this agent is hitting whatever MCP server GitHub compiler lens to do server.  
  
\[Speaker 5\]  
But at Egypt, where the user interacting with the agent doesn't have maybe particular permissions or something that's set up on their end to be able to go hit that MCD server. Well, Mental pole. You can then get some some requests to say, hey, I want to utilize the search underscore Reposi's where his tool within the GitHub co-pilot mcp server, and then somebody can go in, and they can approve that request.  
  
So when you're thinking about elicitation, you're thinking about mid-tool ball. This is. A tool server that the agent may not have access to out of the box by default.  
  
\[Speaker 4\]  
Right. The next piece here is rate limiting again. I know we already talked a little bit about rate limiting, so I won't, uh, muted. That course here with this, but? From a security standpoint, the way I see it outside of costs, right? You want to make sure that? An agent isn't consistently in pots, and we made new requests spending tokens, Etc, but from a security perspective.  
  
If you have an agent that is only supposed to be calling every five seconds or in an hour, it should only be making 60 requests, whatever. But you look at logs, you look at metrics, and you're, like, oh wow, this agent is calling five thousand times. Why is this happening that could be a security implementation, right?  
  
Like, somebody could be, you know, hacking the agent and could be trying to get to various forms of mCP servers tools, whatever they're trying to hit, right again. Point A to point B, so from the? Age into whatever MCP server whatever, so setting up rate limiting again. Aside from the cost aspect of things.  
  
Integrate security implementation as well, which I feel like a lot of people don't think about rate limiting and security sense, but I definitely see it a lot, especially. Like, I said, it's like, hey, I have an agent. Uh, is this Asian supposed to be making 5 000 requests every minute to every single ncp server or every single tool to try and get access.  
  
All right. The next piece is guardrails here, and I'm actually going to do this. No, where is it? All right, move a little. Zoom in here. Okay, so I really like this definition, uh, shout outs already. Oxym guardrails are security policies that inspect LLM requests. And responses to detect and block harmful policy, violating or inappropriate content, or reaches a model or the user.  
  
And the one thing that I want to really point out here is responses, right? I personally, I, I catch myself doing this, too. I'm sure everybody does, but. When you're interacting with an agent, right? You're always thinking about security from the. Going somewhere right, hitting the L1 hitting against the server, hitting another agent.  
  
You're very rarely thinking of how the response is, like when we're thinking about this context as a whole. This is a constant line of communication, right? Your agent is going to hit an llm that MLM, based on your request, is going to go hit nmcp server call a tool and then bring the response back, so you're constantly getting responses back and you need to secure that as well, right?  
  
Because you could go out, you could try and hit something, and the attack Factor could be. Going from point B, point n. So, I really like this with guard rails, and I think this is one of the things that sticks out for me, because like problems, guards rate limiting, um?  
  
\[Speaker 6\]  
Tool.  
  
\[Speaker 4\]  
Uh, tool selection, right in isolation, like, hey, this mcp server has 20 tools, but I only want five to be allowed to be used by this agent. Um, these are all things that, like, kind of, exist, right? And it falls into the guardrails category, but it's not the differentiator for me.  
  
The differentiator is again this piece here. The information that's coming back throughout your context.  
  
Okay, and then speaking of tool isolation. I think this is probably the one that comes up the most for me, because it's um. I want to say the most obvious, but like, I don't. That's probably not the right phrasing for this. This is the one that people are thinking about the most because it's the easiest concept in my opinion to digest right again.  
  
I have an mCP server. This mCP server has 20 tools. I only want five of them allowed by my agent or by a particular user. That's an easy concept to think about right now. One of the things that come up, aside from security in this, is, I believe, the, uh, I believe the number is still between like 15 and 18 tools that you want, uh, exposed to your agent.  
  
Outside of that, you can come up with more and more hallucinations, right? If you have an agent and it's ingesting. 500 tools or whatever right. There could be more hallucinations. There could also be a higher level of. Input zones. So, as your agent is consuming an STP server tools, it's also consuming all of the metadata from those tools, right?  
  
So, if you look at your agent, you say, hey, I've already spent a thousands of tokens before my first input request. Why is that? Well, it could be because your agent is ingesting a whole bunch of tool, um tools, um, the tool descriptions. So, with that being said. There's a couple of different pieces here when we're thinking about tool isolation.  
  
It's what should the agent have access? You. What should the user have access to and there's a couple of different pieces there? From a cost optimization perspectives as well.  
  
\[Speaker 2\]  
This is probably  
  
\[Speaker 4\]  
One of my favorite topics when it comes to security and NCP. I'm also going to show something else as well. It's not in the slides because I literally finished it on the Uber ride here that I can show you the code base. So, has anybody heard of agent identity?  
  
Oh, beautiful, right? Uh, so when we're thinking about Asian identity, we're thinking about. As the name suggests, they probably don't want to explain it all that much, but the identity of the agent, right? Because in this new world, it's not just about the identity of a service, right? So, we're thinking about a service manager.  
  
It's not just the identity of the system, and it's not just the identity of the user. It's the identity of. 10, 20, 30, 40, 100 agents running. I saw, I think it was like, maybe two months ago. I saw this Reddit post, and it was like, we have 40 agents running, and we don't know what happened to do anymore.  
  
It's probably a problem in some capacity, right? Uh, at least, from a cost perspective. So when we're thinking about agent identity, this is again the identity of the agent. Now, more importantly, what the agent can do. So, for example, I have an agent and I'd say, based on who this agent is, maybe it's a read-only agent.  
  
Maybe it's a right only agent. Maybe it's an admin agent. Whatever it is, this agent can then have access to these tools, right. Again, we're I would say in the security space right now. When it comes to mcp, there are a couple of different names, protocols, implementations that maybe overlap a little bit, right?  
  
But there's a couple of different ways to do it, and there's a couple a. Always think about it, and I think that's important because the more options we have, it can be a little bit better. It'd also be worse, so we don't want to have too many options, but we want to have a couple based on our workflows.  
  
But again, I really like this when it comes to Asian identity, because I think originally when the whole idea around agent identity came out. It's, like, okay, great. We now have some maybe workload identity thinking about, like Asian mesh, for example, uh, for this agent, but that's it, right?  
  
We have an identity, great. Now, we have the ability to actually do something with said identity. And if I just do this? Again, this is just something that I finished up on the way here, but this is like a little, uh, Asian mesh demo that I'm putting together. There's the Asian Gateway in here Canadian and istio.  
  
Uh, end. With this right, we have our workload identity based on our service account that's implemented in our mesh. Has anybody here not worked with istio before or any other service mesh with your hand? All right couple people, so I don't want to go into this too much because it could probably take six hours and only everybody will stay here, but But essentially the justice.  
  
When you're thinking about a service measure, thinking about service to service, communication, and how to secure that communication via protocols like mtls  
  
\[Speaker 2\]  
Right now, we can bring  
  
\[Speaker 4\]  
That same approach via workload identity, user agent identities into our intensic infrastructure via something like SEO. So, in this case, for example, what I'm saying is based on this identity, right? This service accounts, it's going to equal the platform. Agent agents or the analytics agent agent and based on its identity, it has access to these tools right, or it has access to this mCP server.  
  
Now, you may be thinking yourself well. Why do I need to go through all this and I just have an expression that specifies the age and name you could,  
  
\[Speaker 5\]  
But the agent name can change the workload identity counts, uh, unless you roll it. But by default, it's not going to change.  
  
\[Speaker 4\]  
Okay, now probably one of the bigger topics here.  
  
Is anybody here not doing anything with authentication authorization and when I say that, I mean logging in and permissions?  
  
\[Speaker 2\]  
Okay, so  
  
\[Speaker 4\]  
When we're thinking about authentication and authorization? Again, very high levels. You log into something that's authentication. What you have the ability to do once you're logged in as long conversation before. And now, our agents and the people using set agents. Need to have this concept as well. Has anybody heard of token exchange?  
  
Of people, all right. Has anybody heard of what we up on behalf? Hello, people. Okay, so? The gist is I have an agent, or I have a user, and this agent is either going to act on behalf of the user with the same permissions and subtract and an authentication authorization or the agent is going to have its own professionals and its own Services value, and when we talk about token exchange, this is the idea of any Hawaii.  
  
Just about any employer Ultra Auto Q Club, whatever there's? Some people that  
  
\[Speaker 5\]  
Yeah,  
  
\[Speaker 4\]  
Here's open  
  
\[Speaker 2\]  
Server.  
  
\[Speaker 4\]  
So, within your Gateway, what you can do is, you can have your Gateway call out with someone SDS.  
  
\[Speaker 5\]  
And get it soaking back. This token is going to have a claim this claim is what you're allowed to do or what the agent is allowed to do what it is access to you. Can it create kubernetes pods and delete kubernetes pods? Is it read only. What  
  
\[Speaker 4\]  
Are these permissions and then we can get into other topics like attribute based access control and relationship based access control, and this concept just it again. This could be a six hour conversation just.  
  
\[Speaker 5\]  
Yeah, nobody wants to be your plot. So  
  
\[Speaker 6\]  
When we're thinking about what an agent can do when we're thinking about what a user can do. This has to follow some off flow, right? So you'll probably see a lot of talk around two things. This is what I see the most at least oydc, based all off. And token exchange.  
  
A lot of stuff around OVO, which I can say OVO slash Focus okay, but?  
  
\[Speaker 5\]  
As we're thinking about all this, and as we're putting this together, right, there's a couple of Concepts. There is.  
  
\[Speaker 6\]  
Mid tool calls, right? So an agent is going to access something in an NCP server. It may not have access to right away. On what the user can do, what the agent can do, and what's possible based on. I had an MCP server what tools are available, right? I have  
  
\[Speaker 5\]  
Xyz permissions. That means my agent shouldn't be able to delete every single kubernetes cluster within my requirements.  
  
\[Speaker 6\]  
And, uh, when we're putting this all together again, in my  
  
\[Speaker 5\]  
Opinion, this really comes down to what your AI Gateway looks like and what options are available. From that area. Gateway because all traffic needs to go through some Gateway somewhere, whether it's you know something like Asian Gateway or something like a Gateway in your cloud provider, regardless of what it is.  
  
Traffic means the opiates get from point A to point B and in the world of mCP and probably agentic as a whole, as it is right now, the majority of what you can secure what you can observe, always sits at ngua or ngua N AI Gateway. Um, sorry. I'm used to saying too much, apparently impulse, uh, okay, so two things that I'll show?  
  
Okay, the first. Is it okay if I put this down?  
  
\[Speaker 2\]  
Yeah, while  
  
\[Speaker 5\]  
I'm typing, yeah,  
  
\[Speaker 1\]  
Hold it for you.  
  
\[Speaker 2\]  
No, it's all good.  
  
\[Speaker 5\]  
If everybody can hear me.  
  
\[Speaker 2\]  
Yeah, yes, all right?  
  
\[Speaker 5\]  
Well, I'm  
  
\[Speaker 3\]  
Just joking, uh,  
  
\[Speaker 5\]  
Okay. So, the first thing is off, right? And this is a very, very simple and small approach to all. So, the first thing that I'm gonna do is go back to my preview window, then I'm going to run this commands right,  
  
\[Speaker 2\]  
And I can  
  
\[Speaker 5\]  
See I have a Gateway here. Readily available public casing, please don't. Send any Nations to attack me all right. The next thing is, I'm going to open up a CP inspector. Is anybody not familiar with MCP inspector budgets? Okay, big everybody's familiar with that, right? It's time to be client.  
  
\[Speaker 2\]  
Oh, all, right, awesome, um?  
  
\[Speaker 5\]  
Oh, actually, that's why it was running in there, uh, let's try that again. You might use the bike, I'm sorry. Yeah, sorry, you sure. Yeah, okay, sorry, yeah, yeah. Sorry.  
  
\[Speaker 2\]  
Harry, will you hear me better? Yeah, no.  
  
I pass this browser somewhere, so I'm gonna just go talk. You don't use real quick. All right. So,  
  
\[Speaker 7\]  
What I'm going to do here is, I'm going to zoom in, and then I'm going to change to streamable HTTP and.  
  
I'm gonna pull up my Gateway address, right? So, I'm going to go over Port 3000. This is just a Gateway that I have set up. It's listening over 3000. The path is Flash MCP.  
  
House and do this.  
  
\[Speaker 2\]  
So okay,  
  
\[Speaker 7\]  
Um?  
  
\[Speaker 2\]  
Because it's a lot.  
  
So entertaining.  
  
It should be up and readily available.  
  
Okay, this  
  
\[Speaker 7\]  
Isn't connecting. That's okay, uh, so effectively. What I can then do is I can set up a policy, and this policy can do your token exchange. It can do OVO, or it could do something as simple as specifying a data that you see, right? So, just some random key.  
  
You can specify on the client and then on the server, and ideally, what will happen, is, you have the ability to authenticate, right. You can disconnect from server and then, when you try to authenticate again, it's going to say. Well, what you can't because you're not there? It's okay, that's that's interesting.  
  
Very basic, JWT based authentication.  
  
\[Speaker 9\]  
Now, the next thing that we will try to do is you go down to elicitation. Okay, so I'm going to pull up.  
  
\[Speaker 2\]  
Okay, so from here, right? I can set up a multiplication to again do that mid tool one, right? So what I want to do is I'm going to go to into Gateway. I'm going to follow my instructions to make sure that I am doing everything I'm supposed to be doing OVO, the agents, and top that open.  
  
And then, I'm going to give it a prompt,  
  
\[Speaker 7\]  
Which is utilizing the getme tool.  
  
\[Speaker 2\]  
Okay, so  
  
\[Speaker 7\]  
Notice here how it says I'm unable to access this tool, right? So, by default, this agent does not have access to this particular tools. Now, what I can do is I can go into Asian Gateway and notice here. Based on this status, I have something a spending. What's pending is the ability for this agent to get this MCP server.  
  
I can go. I can authorize. Should be good to go. Now, I'm going to go ahead on our prompt it again. I don't think I need a new session. All right, boom. And there it is, so that's elicitation in a nutshell, right? You have this mid-tool call where you need to have something or someone approved that request.  
  
That's it. Thanks so much.  
  
\[Speaker 5\]  
Yeah, so  
  
\[Speaker 6\]  
You can have roughly mentioned it at a hidden wavish way up. So I'm kind of curious how you're doing semantic, um, authorizational authentication. How are you doing it at that policy level? Like, I.E, this is stupid. Don't do it, um?  
  
\[Speaker 5\]  
Yeah, yeah, well,  
  
\[Speaker 8\]  
That's usually when it's open. No, um, so that's where we start, but uh, we use something called self. I don't know if you're familiar with it. A common expression language, uh, so essentially what I was showing. I just plucked the Zoom. Apologies, but uh cell, is this expression language that allows you to essentially say like, based on this tool and this  
  
\[Speaker 7\]  
Mcp server only. This agent has the ability to add it. Um, I think that's kind of what you're talking about, right? But I was talking about something even like higher level than that and.  
  
\[Speaker 6\]  
Do some wacky stuff.  
  
\[Speaker 7\]  
Yeah. So  
  
\[Speaker 6\]  
How are you giving them off an occasional authorization based on? Don't do this. Why can't they, like, yeah, I will someone in payment. So say, like, you have one doing transactions. Yeah, so obviously, no, not to give some Nigerian friends, five hundred thousand dollars.  
  
\[Speaker 7\]  
Yeah, uh. So  
  
\[Speaker 2\]  
I would say there's  
  
\[Speaker 7\]  
A couple different pieces there. The first piece, prompt guarding right out of the box. I would say that's probably the, uh, the easiest way to get started and?  
  
\[Speaker 10\]  
I can have a promise card that says something, like, if you have some rejects that says, delete kubernetes flexors, throw a 429, and say, hey, you can delete all these kubernetes clusters, so that's step one step two is. The permissions that the agent has based on what your authorization system looks like, because here's the reality these agents.  
  
\[Speaker 7\]  
Are kind of doing whatever they want right based on how they're set up out of the box by defaults. People using them may just be either a doing, uh, what is it? Command shift shift something, uh, where you turn on auto mode, like quality code or whatever, or you're just hitting, you know, enter.  
  
When it says yes, yes, when it's constantly prompting you, so people aren't really looking at output. And because of that, what the agent has the ability to do needs to happen behind the scenes, and I see this in three ways standard relationship-based access control, right? So this agent or this user isn't.  
  
And their read-only group, or they only have access to this region or whatever right relationship based access control. So this person using this agent has this manager. Therefore, they only have access to these files. That's a, that's a handy way. We would talk about relationship-based access control and attribute based access control.  
  
And this is the one that I see the most when it comes up, especially around M. So, after you based access control would be something along the line. Job. I live in New Jersey, therefore my working hours are dining and clock via. During  
  
\[Speaker 3\]  
Those hours, I have  
  
\[Speaker 7\]  
Root level access to any kubernetes cluster that I want. But before 9 A.M and after 5 PM, I do not have access based on my geographical location, right, which is actually this access control of a nutshell. Anything? Uh, like, if you have a policy enforcement tool and policy engines or Alverno or whatever you're using, that's attribute based access control.  
  
So already, we hold policy, of course, right? But you can do the same thing. Silence, your question? Yeah, yeah, okay, beautiful. Thank you.  
  
\[Speaker 8\]  
Okay,  
  
\[Speaker 6\]  
Questions. Have you have a larger  
  
\[Speaker 8\]  
L o n kind of Hoover denied the request or the agent  
  
\[Speaker 6\]  
Supposed per tool?  
  
\[Speaker 7\]  
Sorry, one more time,  
  
\[Speaker 6\]  
A  
  
\[Speaker 8\]  
Larger llm approval, deny the replays in ancient series and boom pole. Yeah, so how would it approver deny? Essentially, you're asking, okay?  
  
\[Speaker 1\]  
That.  
  
\[Speaker 7\]  
That agent then goes and hits whatever L1. Now, based on what you're asking, your agent's doing your prompt, it's then going to go and say, oh, hey,  
  
\[Speaker 10\]  
Llm. I need to go hit this MCP server, right? And then, it's going to utilize whatever tool. So, the question around? Can an llm block the call? That's really where something like tool isolation will come into play like that should happen before it even gets to the L and to make it.  
  
Decision, like that, should be happening a couple of steps prior. Yeah, and that's really tool. Isolation comes into play. That's where, hey, I have this ancient identity, or I have this, uh, workload identity within my agent mesh does is agents have access to these tools gay or nay, right?  
  
Like, this policy is going to be kicked off way before the llm has to make maintenance soon.  
  
\[Speaker 5\]  
Hey, uh, sorry to ask you a question.  
  
\[Speaker 7\]  
But no, no, please, you want to. Mike, thanks. So, what are the interesting, like?  
  
\[Speaker 5\]  
Situations where your mCP server has a variety of different plugins, um, and those clients, the customer. When you have different sort of certifications, so, there are levels of being that they can access, right? So, let's say, you know, your department of health you have called, and you have charging PT and have some internal tool.  
  
Includers allowed to access Health Data. LGBT is not allowed to access Health data, but it's allowed to access, you know, so? The data, and then your internals aren't there. Just access everything, right? Um, as a MC Visa will provider, you have to be aware of which client is calling you so that you can be hopeful about what either you're willing to return in a response to that client, right?  
  
Uh, yeah. My question, is that? Do you have a recommendation or a story about MTP server provider like establishers and put it into Google client is such that you could be thoughtful about what the idea you're returning at that point. Yeah, so  
  
\[Speaker 7\]  
I'll I'll play Devil's Advocate for a second, and please feel free to tell me I'm wrong.  
  
No, you're good.  
  
\[Speaker 2\]  
I think that's all  
  
\[Speaker 6\]  
Okay. Thank you so playing Devil's Advocate person. I would actually say that that's not the job of the mCP server, right? So an mcp server as a whole is like, this is a black box, right? Um, like, during kubecon, uh? 2025, I think North America was having a conversation with customer, and they were like, well.  
  
How do we know? At this mCP server, secure, right? Like, what can we do about it? I'm, like, well, you can't do anything like you can then test it. But like, I'm sure, GitHub, and whoever else isn't going to like you, uh, doing that to their mcp servers, right?  
  
So, like, this is just a black box of information.  
  
\[Speaker 8\]  
So, what you have to do is instead of putting that harness on the mcp server, right? You have to take that a step back and put those decisions in your Gateway again. Things like tool isolation, things like what agent can do, what it can do, what it has the ability to access based on its own identity, based on some type of workload identity, um, whatever it is like, that has to happen prior.  
  
And I would say, just because, again, because I'm I'm biased, right? I work in the space, but I think that that happens at the Gateway right now. Can also happen at let's say, for example, the harness, right? Like, you can set configuration specifications to say this harness can access this MTP server, these tools, Etc, but?  
  
How do you actually enforce that? I'll give you an example, right? Like, somebody goes into my open code configuration, right? And, uh, they say, hey, you have to go through this Gateway. Well, I can just take that out. All right, just edit, edit file, and boom, right now. I can go and hit anything I want.  
  
But if you have your policies, your configurations, your security, your governance, whatever wallet at the Gateway level right, and you're setting policies for all agents. All harnesses to go through that giveaway. Everything's going to always be automatically  
  
\[Speaker 2\]  
Stopped right there sure. Yeah, yeah, that? So, so that makes sense, but I, I don't think it like.  
  
\[Speaker 6\]  
Fireflies that he owns it to me in my head. So, if I understand what you're saying correctly, it's like, okay, well, rather than pointing chord and chapter. You can see it there MTP server directly. I want to point in it again, right? But ultimately, the Gateway still needs a mechanism of like, probably knowing what the client is, uh, in order to like establish on it, you know whether it can return epitheater or not in.  
  
In response, I saw when you talk the idea of like these. Awts being provided by the agents, and like, maybe you could use that to do the same thing. But, you know, the client is cool. Like, you always calling the force that they're going to give you a particular AWT, right?  
  
Yeah, yep.  
  
\[Speaker 8\]  
So, the, uh so, so the JWT stuff I'll say it's a really small and simple example to show authentication, right? So, like, nobody's ever going to join anything like, uh, you know? If you have a thousand agents, you're gonna have a thousand jwts and that you're going to manually put those into yaml configurations.  
  
Maybe there's somebody out there, but I'm not interested in being that person. So, what I'm going to do is I'm going to put that bonus on OVO or token exchange. Along those Library, I want to exchange some token, and I want to get that claim back based on whatever permissions I have or  
  
\[Speaker 3\]  
The Asian test.  
  
\[Speaker 8\]  
Okay, that's always going to come a step prior. Now, I think one of the questions that you're kind of alluding to as well is, like, I have codex. I have called code. I have open code I have brought. I have whatever. How can I force that client to go through this Gateway  
  
\[Speaker 6\]  
And identify itself? Yeah,  
  
\[Speaker 8\]  
So identifying themselves, uh, I'll send you the git repo connect with me on LinkedIn. I'll send it to you, but the stuff that I've created today on the on the, uh, car, right over. Here is something called Asia mesh that we're all right, and agent Mash is essentially you, um, enroll your service accounts or your name spaced.  
  
Discount system into a mesh, right? You then have a spiny idea? Very respirator who's expired, and then that identity is what the agent has is its identity. Because you're spinning up the agent with that service count. I'm talking about instrument kubernetes perspective, by the way, because does the underlying platform that I work in.  
  
So, because that service count is a split, the ID. The Asian dinners with the idea, because I'm starting the agents via what is service count. So that's so the ID originates in that form, for example. Therefore, we're going in that direction. We'll look at each time it isn't their stuff.  
  
Yeah, super excellent. I'd love to connect the game. Yeah, thank you so much.  
  
\[Speaker 9\]  
All right, I'm gonna get through a little bit  
  
\[Speaker 2\]  
More housekeeping. First things  
  
\[Speaker 1\]  
First is landscape data dog, another round of applause.  
  
Oh, okay, um. So, with our appreciation for data Dom's generosity, we agreed to be great guest, right? There are guests in their home. We're going to clean up behind ourselves. We are going to trash the place when we're walking out, right? Um. Also. We have cake. Francis is that it must be K, and we're gonna have a party.  
  
So we do have Kate available as well, and I wanted to just tell you all about. If one more of these types of conversations we have several events that the agency AI Foundation, uh? So, it's on. We have big agent con slash NCP con happening in San Jose in October, uh.  
  
We would love for you all to come. I think that the tickets are pretty reasonable, but I also can give you a 15, um. Little Angie discount. All right, uh, if we could get the slides back up, and if not, I would just have to tell you. And your family number.  
  
There's also one in. Amsterdam. If you all like to travel, but otherwise. You can come and join us in San Jose. Anyone have the? Let me see, I gotta find my message.  
  
Y'all, getting y'all paper and pants out? But he gave me the discount code.  
  
Did somebody say discount for what?  
  
All right. So, the if you go to AIF dot IO slash events, that's the events, uh, where all of the links to the event and your code is.  
  
\[Speaker 3\]  
Drum  
  
\[Speaker 1\]  
Roll.  
  
Wow\! This is so easy. I'm so impressed. It's Meetup 15, right? So, that's your code. Okay, anything else I need to mention? You said aaif a i f-i-o? Flash events. Escape, which one you want put in? Meet up 15 for your cold, uh? For 15 off Ranger collie, there we go okay.  
  
Oh, this is the other thing I have to say. So, we are also a remember, just again Foundation non-profit under Lenny's Foundation founded by Islamic open AI and block has created the first official mcp certification. If you came here tonight, that's step one. And then, like an mCP. Guru.  
  
So, uh? Thank you so much. So, if you want to take that certification, this is the scan we are working on the exam now. Uh, it's gonna be actually being beta testing for beta testing. This is for the adventures, so this is not the final version of the test, but if you take it and you pass it, you will be certified.  
  
This one is at a reduced rate to take it, but then we're going to modify the exam after that. So, this, you don't get a retake on this one. So, this is for. And be, like, oh, I know my stuff. I can take it. No problem. If you're somebody who was, like, oh, I don't know, I might do well, see what's on there, and then I'm gonna come back and take it again.  
  
Don't take this right, but go ahead and sign up if you want to do the beta one. Just let me know, and I can put you on a list,  
  
\[Speaker 2\]  
Um.  
  
\[Speaker 1\]  
But yeah, if you also sign up for one of the events, then you can add this as well for a discounted rate. Okay, I can't move the slides, but I already gave y'all the event discount Meetup 15, and I think we're ready for cake.  
  
\[Speaker 2\]  
A1k me too. Okay, that's the event links for anybody. Okay.  
  
It's okay. Podcast.  
  
\[Speaker 7\]  
That might be it.  
  
\[Speaker 1\]  
Oh, okay, oh yes, the podcast, very good. Thank you so, um, my colleague demetrios, who leads, um, ml Ops Community, has a podcast under aeiya. It's called agenda conversations, so definitely check that out as well. We have, uh, all sorts of wonderful people in the ginsengai Community. Come on and talk about cool stuff that they're doing.  
  
All right now. Give me a  
  
\[Speaker 2\]  
Cake all right. So much for coming out. I'm very happy baby organizes. He took them around in the fall. To your local area. So thankful for now, all right.  
  
You shouldn't be trying to grow that way, but what we are doing. Oh bro, here's one here. Let's take a picture. Yeah.