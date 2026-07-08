# Transcript: Skill Issue — Andrej Karpathy on Code Agents, AutoResearch, and the Loopy Era of AI

**Source:** https://youtu.be/kwSVtQ7dziU

---

[00:00:00.000] Code's not even the right verb anymore,

[00:00:01.880] right? [laughter] But I have to

[00:00:03.640] express my will to my agents for 16

[00:00:06.240] hours a day. Manifest. [music]

[00:00:07.760] How can I have not just a single session

[00:00:09.280] of Claude code or Codex or some of these

[00:00:10.880] agent harnesses? How can I have more of

[00:00:12.560] them? How can I do that appropriately?

[00:00:14.640] The agent part is now taken for granted.

[00:00:16.480] Now the claw-like entities are taken for

[00:00:18.080] granted and now you can have multiple of

[00:00:19.640] them and now you can have instructions

[00:00:21.120] to them and now you can have

[00:00:22.240] optimization over the instructions. But

[00:00:24.000] there

[00:00:24.235] >> [laughter]

[00:00:24.480] >> I mean this is why it gets to the

[00:00:25.360] psychosis is that this is like infinite

[00:00:27.080] and everything is a skill issue.

[00:00:34.800] Hi listeners, welcome back to No Priors.

[00:00:37.000] Today I'm here with Andre Karpathy and

[00:00:38.800] we have a wide-ranging conversation for

[00:00:40.480] you about code agents, the future of

[00:00:43.000] engineering and AI research, how more

[00:00:45.160] people can contribute to research,

[00:00:47.200] what's happening in robotics, his

[00:00:49.160] prediction for how agents can reach out

[00:00:51.090] [music] into the real world, and

[00:00:53.080] education in this next age. Welcome,

[00:00:55.240] Andre.

[00:00:56.200] Andre, thanks for doing this. Yeah,

[00:00:57.760] thank you for having me.

[00:00:59.080] Uh so it's been a very exciting couple

[00:01:01.040] of months in AI. Uh yeah, you could say

[00:01:03.440] that.

[00:01:03.800] >> I remember um walking into the office at

[00:01:07.160] some point and you were like really

[00:01:08.240] locked in and I was asking what you were

[00:01:10.360] up to and you're like, I just I have to

[00:01:11.680] code for 16 hours a day or code's not

[00:01:13.600] even the right verb anymore, right? But

[00:01:15.520] I have to

[00:01:16.680] um express my will to my agents for 16

[00:01:19.440] hours a day. Manifest

[00:01:21.600] um because like there's been a jump in

[00:01:24.000] capability.

[00:01:25.640] Uh what's happening? Tell me about your

[00:01:26.920] experience. Yeah, I kind of feel like I

[00:01:28.760] was just in this perpetual I still am

[00:01:30.520] often in this state of AI psychosis just

[00:01:32.800] like all the time um because there was a

[00:01:34.800] huge unlock in what you can achieve as a

[00:01:36.200] person as an individual, right? Because

[00:01:37.800] you were bottlenecked by, you know, your

[00:01:39.320] typing speed and so on. But now with

[00:01:41.240] these agents it really, I would say in

[00:01:42.960] December is when it really just

[00:01:45.160] something flipped where I kind of went

[00:01:46.720] from 80/20 of like, you know, uh to like

[00:01:49.040] 20/80 of writing code by myself versus

[00:01:51.360] just delegating to agents. And I don't

[00:01:53.000] even think it's 20/80 by now. I think

[00:01:54.360] it's a lot more than that. I don't think

[00:01:55.520] I've typed like a line of code probably

[00:01:58.360] since December basically.

[00:01:59.866] >> [laughter]

[00:02:00.600] >> Um which is like an extremely large

[00:02:03.320] uh change. Um I was talking to it like

[00:02:05.760] for example, I was talking about it to

[00:02:07.520] for example my parents and so on and I

[00:02:09.320] don't think like a normal person

[00:02:10.200] actually realizes that this happened or

[00:02:11.680] how dramatic it was. Like literally like

[00:02:13.680] if you just find a random software

[00:02:15.040] engineer or something like that at their

[00:02:16.480] at their desk and what they're doing,

[00:02:17.840] like their default workflow of, you

[00:02:20.000] know, building software is completely

[00:02:22.000] different as of basically December.

[00:02:24.560] Uh so I'm just like in this state of

[00:02:26.720] psychosis of trying to figure out like

[00:02:28.440] what's possible, uh trying to push it to

[00:02:30.360] the limit. How is it how can I have not

[00:02:31.920] just a single session of, you know, um

[00:02:33.840] Claude code or Codex or some of these

[00:02:35.240] agent harnesses? How can I have more of

[00:02:36.880] them? How can I do that uh

[00:02:38.440] appropriately? And then how can I use

[00:02:40.640] these claws? What are these claws? Uh

[00:02:43.080] and uh so there's like a lot of new

[00:02:45.120] things. I want to be at the forefront of

[00:02:46.840] it, you know, and I'm very

[00:02:48.360] antsy that I'm not at the forefront of

[00:02:49.880] it and I see lots of people on Twitter

[00:02:51.120] doing all kinds of things and they all

[00:02:52.200] sound like really good ideas and I need

[00:02:53.560] to be at the forefront or I feel

[00:02:54.880] extremely nervous. And so I guess I'm

[00:02:56.480] just in this psychosis of like what's

[00:02:58.080] possible like because it's unexplored

[00:03:00.000] fundamentally. Well, if you're nervous,

[00:03:01.400] the rest of us are are nervous. We have

[00:03:03.520] a we have a team that we work with at

[00:03:05.760] Conviction that their setup is everybody

[00:03:08.880] is like, you know, none of the engineers

[00:03:11.000] write code by hand and they they're all

[00:03:13.360] microphoned and they just like whisper

[00:03:14.920] to their agents all the time. It's the

[00:03:16.560] strangest work setting ever.

[00:03:18.920] Uh and I thought they were crazy and now

[00:03:20.520] I like I fully accept I was like, oh

[00:03:21.920] this was the way. Like you're just ahead

[00:03:23.480] of it.

[00:03:24.440] Um what uh

[00:03:26.240] how do you think about your own capacity

[00:03:27.960] now to like explore or to do projects?

[00:03:30.680] Like what is it limited by?

[00:03:32.720] Yeah, what is it limited by? Uh just I

[00:03:34.360] think everything like so many things

[00:03:36.480] even if they don't work, I think to a

[00:03:38.280] large extent you feel like it's a skill

[00:03:39.600] issue. It's not that the capability is

[00:03:41.040] not there. It's that you just haven't

[00:03:42.200] found a way to string it together of

[00:03:44.320] what's available. Like I just don't I

[00:03:45.960] didn't give good enough instructions in

[00:03:47.840] the agents from the file or whatever it

[00:03:49.920] may be. I don't have a nice enough

[00:03:51.920] memory tool that I put in there or

[00:03:53.920] something like that. So it all kind of

[00:03:55.560] feels like skill issue when it doesn't

[00:03:56.600] work to some extent. You want to see how

[00:03:58.160] you can parallelize them etc. and you

[00:03:59.800] want to be Peter Steinberg basically. Uh

[00:04:01.960] so Peter is famous. He has a funny photo

[00:04:03.760] where he's in front of a monitor with

[00:04:04.960] lots of uh like he uses Codex. So lots

[00:04:07.400] of Codex agents tiling the the monitor

[00:04:10.040] and they all take about 20 minutes if

[00:04:11.360] you prompt them correctly and use the

[00:04:12.840] high effort. And so they all take about

[00:04:14.320] 20 minutes. They have multiple, you

[00:04:15.720] know, 10 repos checked out. And so he's

[00:04:18.560] just um going between them and giving

[00:04:20.680] them work. It's just like you can you

[00:04:22.240] can you can move in much larger macro

[00:04:24.280] actions. It's not just like here's a

[00:04:25.720] line of code, here's a new function.

[00:04:27.000] It's like here's a new functionality and

[00:04:29.240] delegate it to agent one. Here's a new

[00:04:30.600] functionality that's not going to

[00:04:31.480] interfere with the other one. Give it

[00:04:32.800] agent two. And then try to uh review

[00:04:35.320] their work as best as you can

[00:04:37.068] >> [laughter]

[00:04:37.480] >> depending on how much you care about

[00:04:38.440] that code. Like where are these macro

[00:04:40.000] actions that I can like manipulate my

[00:04:41.760] software repository by? And like another

[00:04:44.440] agent is doing some like research,

[00:04:45.880] another agent is writing code, another

[00:04:47.320] one is coming up with a plan for some

[00:04:48.640] new implementation. And so everything is

[00:04:50.320] just like happens in these like macro

[00:04:51.960] actions over your repository. Um and

[00:04:54.840] you're just trying to become like really

[00:04:56.120] good at it and develop like a muscle

[00:04:57.600] memory for it is extremely um

[00:05:00.480] Yeah, it's very rewarding number one

[00:05:01.840] because it actually works. Uh but it's

[00:05:03.320] also kind of like the new thing to

[00:05:04.360] learn. So that's why hence the

[00:05:06.080] psychosis.

[00:05:07.400] Yeah, I I do feel like my instinct is

[00:05:10.320] like

[00:05:11.280] whenever I'm waiting for an agent to

[00:05:12.880] complete something, the obvious thing to

[00:05:14.280] do is like, well, I can do more work,

[00:05:15.960] right? Like if I have access to more

[00:05:17.440] tokens then like I should just

[00:05:19.040] parallelize at tasks. And so that's

[00:05:21.400] that's very stressful because if you

[00:05:23.440] don't feel very bounded by your ability

[00:05:25.360] to spend on tokens, then you know, you

[00:05:28.320] are the bottleneck in the system that is

[00:05:30.000] max capability. Yeah, if you're not

[00:05:31.400] maximizing your subscription at least.

[00:05:33.960] And

[00:05:34.720] ideally for multiple agents. Like if you

[00:05:36.360] run out of the quota on Codex, you

[00:05:38.000] should switch to Claude or whatnot. I

[00:05:39.280] don't know. Like that's what I've been

[00:05:40.520] trying to do a little bit and I feel

[00:05:42.040] nervous when I have subscription left

[00:05:43.480] over. That just means I haven't

[00:05:45.000] maximized my token throughput. So I

[00:05:47.040] actually kind of experienced this when I

[00:05:48.080] was a PhD student. You would feel

[00:05:49.320] nervous when your GPUs are not running.

[00:05:51.200] Like you have GPU capability and you're

[00:05:52.480] not maximizing your the available flops

[00:05:54.120] to you. But now it's not about flops,

[00:05:55.640] it's about tokens.

[00:05:56.960] So what is your token throughput and

[00:05:59.320] what token throughput do you command? I

[00:06:01.360] would actually argue that it's very

[00:06:02.680] interesting that we had, you know, at

[00:06:05.280] least 10 years where

[00:06:07.960] in many engineering tasks people just

[00:06:09.720] did they didn't feel compute bound.

[00:06:11.960] Right? Um and now the entire industry

[00:06:14.200] feels that now. They feel like they they

[00:06:16.360] they felt resource bound uh

[00:06:18.760] and now that you have this big

[00:06:20.560] capability jump, you're like, oh,

[00:06:22.960] actually it's not, you know, my ability

[00:06:24.760] to access the computer anymore. Like I'm

[00:06:26.760] I'm the binding constraint. Yeah, it's a

[00:06:28.240] skill issue. Which is very empowering

[00:06:30.440] cuz um yeah, cuz you could be getting

[00:06:32.240] better. So that's why that's why I think

[00:06:34.080] it's very addictive because there's

[00:06:35.360] unlocks when you when you get better.

[00:06:36.880] Where do you think it goes? Like if you

[00:06:38.440] just think about like, okay, you know,

[00:06:40.880] Andre's iterating and everybody else is

[00:06:42.760] for 16 hours a day getting better at

[00:06:44.160] using coding agents. Like what does it

[00:06:45.400] look like in a year?

[00:06:46.720] Of like you've reached mastery.

[00:06:48.724] >> [laughter]

[00:06:49.080] >> Yeah, what does mastery look like,

[00:06:50.160] right? At the end of the year or like

[00:06:52.120] two, three years, five years, 10 years,

[00:06:53.400] etc.

[00:06:54.640] Well, I think everyone is basically

[00:06:55.520] interested in like going up the stack.

[00:06:57.880] So I would say it's yeah, it's not about

[00:06:59.640] a single session with your agent.

[00:07:01.920] Multiple agents, how do they collaborate

[00:07:03.280] and teams and so on. So everyone's

[00:07:05.080] trying to figure out what that looks

[00:07:06.000] like. And then I would say Claude is

[00:07:07.440] also kind of an interesting direction

[00:07:08.600] because it really, when I say a Claude,

[00:07:10.280] I mean this like layer that kind of

[00:07:12.160] takes persistence to a whole new level.

[00:07:13.960] Like it's something that like keeps

[00:07:15.480] looping. It's it's like um

[00:07:17.440] it's not something that you are

[00:07:18.560] interactively in the middle of. It kind

[00:07:20.200] of like has its own little sandbox, its

[00:07:22.200] own little

[00:07:23.400] you know, it kind of like does stuff on

[00:07:24.760] your behalf even if you're not looking

[00:07:26.080] kind of thing.

[00:07:27.200] Um and then also has like maybe more

[00:07:29.200] sophisticated memory systems etc. that

[00:07:30.760] are not yet implemented in agents. So

[00:07:33.000] um Open Claude has a lot more

[00:07:34.120] sophisticated memory I would say than

[00:07:35.360] what you would get by default uh which

[00:07:37.120] is just a memory compaction when your

[00:07:38.560] context runs out, right? You think

[00:07:40.120] that's the piece that resonated for more

[00:07:42.000] users versus like perhaps like broader

[00:07:44.360] tool access? For Open Claude? Yeah. Uh

[00:07:46.880] there's like I think there's at least

[00:07:48.120] five things that are really good ideas

[00:07:49.160] in here. Yeah, good job, Peter. I mean

[00:07:51.000] Peter has done a really amazing job. Um

[00:07:53.280] I saw him recently. Uh and I talked to

[00:07:55.920] him about it and I he's very humble

[00:07:57.600] about it. But I think he

[00:08:11.600] innovated simultaneously in like five

[00:08:12.800] different ways and put it all together.

[00:08:14.600] Um so for example like the soul and D

[00:08:16.160] document. Like he actually really

[00:08:17.960] crafted a personality that is kind of

[00:08:19.360] compelling and interesting. And I feel

[00:08:20.680] like a lot of the current agents they

[00:08:21.720] don't get this correctly. I actually

[00:08:23.160] think a Claude has a pretty good

[00:08:24.160] personality. It feels like a teammate

[00:08:26.280] uh and it's excited with you etc.

[00:08:29.000] I would say um for example Codex is a

[00:08:30.880] lot more dry um which is kind of

[00:08:33.159] interesting because [laughter] in it's

[00:08:34.240] true. You know, it doesn't it

[00:08:36.479] and the other thing I would say is for

[00:08:37.919] example with Claude I think they dialed

[00:08:39.280] the sycophancy fairly well where when

[00:08:41.320] Claude gives me praise, I do feel like I

[00:08:43.000] slightly deserve it because sometimes I

[00:08:44.840] kind of give it like not very well

[00:08:46.000] formed thoughts and uh I give it an idea

[00:08:48.320] that I don't think it's fully baked and

[00:08:49.680] it doesn't actually react very strongly.

[00:08:51.000] It's like, oh yeah, we can implement

[00:08:52.400] that. But when it's a really good idea

[00:08:54.360] by my own account, it does uh seem to

[00:08:56.640] reward it a bit more. And so I kind of

[00:08:58.280] feel like I'm trying to like earn its

[00:08:59.840] praise which is really weird. And so I

[00:09:01.760] do think the personality matters a lot

[00:09:03.480] uh and I think a lot of the other uh

[00:09:05.080] tools maybe don't appreciate it as much.

[00:09:06.640] And I think in this aspect also Peter

[00:09:08.080] really cares about this and so that was

[00:09:09.560] correct. And then the memory system and

[00:09:11.360] then uh just, you know, he's just having

[00:09:13.480] fun with this um and then the the single

[00:09:15.760] WhatsApp portal to all of the

[00:09:16.920] automation.

[00:09:17.560] >> Yeah. Is there something that you have

[00:09:19.960] done personally with your claws beyond

[00:09:23.320] software engineering that you think is

[00:09:24.720] fun or interesting? Yeah, so in January

[00:09:26.440] I had a claw I went through a period of

[00:09:28.280] claw psychosis. So I built um I have a

[00:09:30.720] claw basically that takes care of my

[00:09:32.520] home and I call him Dobby the elf uh

[00:09:34.760] claw.

[00:09:35.760] Um and uh basically I used uh the agents

[00:09:39.360] to find all of the smart home subsystems

[00:09:42.000] of my home on the local area network

[00:09:44.080] which I was kind of surprised that it

[00:09:45.080] worked out of the box. Like I just told

[00:09:46.360] it that I think I have Sonos at home.

[00:09:47.760] Like can you try to find it? And it goes

[00:09:49.480] and it did like IP scan of all of the um

[00:09:52.040] basically um computers on the local area

[00:09:54.160] network and and found the Sonos thing uh

[00:09:56.200] the Sonos uh, system and it turned out

[00:09:59.240] that there's no password protection or

[00:10:00.560] anything like that. It just logged in

[00:10:01.560] and it's like, "Oh, yeah, you have these

[00:10:02.400] Sonos systems installed. I Let me try to

[00:10:04.560] reverse engineer how it's working." It

[00:10:06.320] does some web searches and it finds

[00:10:07.800] like, "Okay, these are the API

[00:10:08.720] endpoints." And then it's like, "Do you

[00:10:10.520] want to try it?" And I'm like, "Whoa,

[00:10:11.720] like you just did that." And I'm like,

[00:10:12.640] "Yeah, can you try to play something in

[00:10:13.920] the study?" And, uh, it does and music

[00:10:16.120] comes out and I'm like, "I can't believe

[00:10:17.680] I just That's crazy. That's like three

[00:10:19.280] prompts. Yeah.

[00:10:19.960] >> I can't believe I just typed in like,

[00:10:20.960] "Can you find my Sonos?" and then

[00:10:22.080] suddenly it's playing music. And it did

[00:10:23.680] the same for lights. And so like it kind

[00:10:26.080] of hacked in, figured out the whole

[00:10:27.160] thing, uh, created APIs, created

[00:10:29.080] dashboard so I could see the command,

[00:10:31.040] uh, kind of center of like all of my

[00:10:32.280] lights in the home. And then it was like

[00:10:33.800] switching lights on and off and, you

[00:10:35.400] know, so I can ask it like, "Dobby, it's

[00:10:37.560] sleepy time." And when it's sleepy time

[00:10:39.360] that just means all the lights go off,

[00:10:40.720] etc. and like so on. So it controls all

[00:10:42.920] of my lights, my HVAC, my shades, uh,

[00:10:45.560] the pool and, uh, the spa and also my

[00:10:47.680] security system. So I have a camera

[00:10:49.280] pointed outside of the house and anytime

[00:10:51.360] someone rolls in I have a Quinn, uh,

[00:10:54.240] a Quinn, uh, model that looks at the

[00:10:55.720] videos. So first of all there's change

[00:10:57.480] detection. Right.

[00:10:58.560] >> And then based on change detection it

[00:10:59.600] goes to Quinn and then it actually like

[00:11:01.360] tells me, um, it sends me a text to my

[00:11:03.560] WhatsApp. It shows an image from the

[00:11:05.520] outside and it says, "Hey, a FedEx truck

[00:11:07.960] just pulled up. FedEx truck just pulled

[00:11:09.880] up and you might want to check it and

[00:11:11.320] you got new mail or something like

[00:11:12.360] that." And Dobby just text me this. This

[00:11:14.360] is really incredible. Um, so so Dobby is

[00:11:17.839] in charge of the house. I text through

[00:11:19.520] with it through WhatsApp, um,

[00:11:21.560] and it's been like really fun to have

[00:11:23.080] these macro actions that maintain my

[00:11:24.880] house. I haven't like really pushed it,

[00:11:26.600] uh, like way more beyond that and I

[00:11:28.000] think people are doing a lot more crazy

[00:11:29.240] things with it, uh, but for me even just

[00:11:30.920] the home automation setup I used to use

[00:11:32.400] like six apps, uh, completely different

[00:11:34.200] apps and I don't have to use these apps

[00:11:35.360] anymore. Like Dobby controls everything

[00:11:36.920] in natural language. It's amazing. Um,

[00:11:39.520] and so I think like I haven't even

[00:11:40.760] pushed the paradigm fully but already

[00:11:42.800] that is so helpful and so inspiring I

[00:11:44.720] would say. Do you think that's

[00:11:45.880] indicative of like what people want from

[00:11:47.520] a user experience perspective with

[00:11:49.080] software, right? Because I I don't

[00:11:50.720] think, you know, it's pretty ignored

[00:11:52.680] that it takes humans effort to like

[00:11:54.440] learn new software, like new UI. Yeah. I

[00:11:57.680] think, uh, to some extent that's right.

[00:11:59.920] It's like working backwards from how

[00:12:01.120] people think an AI should be because

[00:12:04.160] what people have in their mind of like

[00:12:05.720] what an AI is is not actually what an

[00:12:07.080] LLM is by by like in the raw sense. Like

[00:12:09.720] LLM is a token generator, you know, like

[00:12:11.160] more tokens come out. But what they

[00:12:12.600] think of is like this

[00:12:13.920] this persona identity that they can tell

[00:12:16.320] stuff and it remembers it, you know?

[00:12:18.520] And, uh, it's just kind of an entity

[00:12:19.880] behind the WhatsApp. It's like a lot

[00:12:21.000] more understandable. Mhm. Uh, so I think

[00:12:23.760] to some extent it's like matching the

[00:12:25.000] expectations that humans already have

[00:12:26.400] for what an AI should behave but under

[00:12:27.800] the hood it's like a lot of technical

[00:12:29.000] details go into that. And LLMs are too

[00:12:30.760] raw of a primitive, uh, to actually, um,

[00:12:34.080] type check as AI I think for most people

[00:12:36.320] if that makes sense. Yeah. Um, I think

[00:12:38.120] that's like how we understand what the

[00:12:39.800] AI is and like the, um, description of

[00:12:43.320] it as Dobby or some persona obviously

[00:12:46.280] resonates with people. Um, I also think

[00:12:48.520] that it it

[00:12:50.040] uh, the unification that you did across

[00:12:52.200] your six different software systems for

[00:12:53.680] your home automation speaks to a

[00:12:55.400] different question of like

[00:12:56.920] do people really want all of the

[00:12:57.920] software that we have today? Yeah.

[00:12:59.640] Right? Um, because I I would argue like,

[00:13:01.560] well, you have the hardware but you've

[00:13:03.640] now thrown away the software or the UX

[00:13:06.480] layer of it. Um, do you think that's

[00:13:08.760] what people want? Yeah, I think there's

[00:13:10.400] this like

[00:13:11.560] there's this sense that these apps that

[00:13:12.920] are on the app store for using these

[00:13:14.560] smart home devices, etc. Uh, these

[00:13:16.560] shouldn't even exist kind of in a

[00:13:17.839] certain sense. Like shouldn't it just be

[00:13:19.240] APIs and shouldn't agents be just using

[00:13:21.600] it directly? And, um, wouldn't it like I

[00:13:25.640] can do all kinds of home automation

[00:13:26.800] stuff that, uh, in any individual app

[00:13:28.680] will not be able to do, right? Um, and

[00:13:30.440] an LLM can actually drive the tools and

[00:13:32.000] call all the right tools and do uh, do

[00:13:33.600] pretty complicated things. Um,

[00:13:35.920] and so in a certain sense it does point

[00:13:38.240] to this like maybe there's like an

[00:13:39.720] overproduction of lots of custom bespoke

[00:13:41.480] apps that shouldn't exist because agents

[00:13:43.560] kind of like crumble them up and

[00:13:45.680] everything should be a lot more just

[00:13:46.839] like exposed API endpoints and agents

[00:13:49.080] are the glue of the intelligence that

[00:13:51.240] actually like tool calls all the all the

[00:13:53.080] parts. Um, another example is like my

[00:13:55.360] treadmill. Uh, there's an app for my

[00:13:56.920] treadmill and I wanted to like keep

[00:13:58.520] track of how often I do my cardio, uh,

[00:14:00.480] but like I don't want to like log into

[00:14:02.160] web UI and go through a flow and etc.

[00:14:04.640] Like all this should just be like make

[00:14:06.040] APIs available and this is kind of, you

[00:14:08.120] know, going towards the agentic, um,

[00:14:10.520] sort of web or like agent first, uh,

[00:14:12.320] tools and all this kind of stuff. So I

[00:14:13.839] think the industry just has to

[00:14:15.079] reconfigure in so many ways that's like

[00:14:16.720] the customer is not the human anymore.

[00:14:18.040] It's like agents who are acting on

[00:14:19.640] behalf of humans and this refactoring

[00:14:21.440] will be will probably be substantial in

[00:14:23.400] a certain sense. One way that people

[00:14:25.120] sometimes push back on this is like, do

[00:14:26.880] people Do you Do we expect people to

[00:14:28.360] write code some of these tools? Do we

[00:14:30.240] expect normal people to do this kind of

[00:14:32.160] stuff that I described? Mhm. But I think

[00:14:33.920] to some extent

[00:14:35.240] this is just, you know, technology as it

[00:14:36.480] exists today and right now there is some

[00:14:38.200] write coding and I'm actually watching

[00:14:39.760] it and I'm working with the system but I

[00:14:42.160] kind of feel like this kind of stuff

[00:14:43.360] that I just talked about this should be

[00:14:45.160] free like in a year or two or three.

[00:14:47.520] There's no write coding involved. This

[00:14:48.800] is trivial. This is table stakes. This

[00:14:50.400] is like any AI, even the open source

[00:14:52.360] models, etc. can like do this. You

[00:14:54.120] should be able to translate it from a

[00:14:56.200] less technical humans intent very easily

[00:14:59.079] to this outcome.

[00:15:00.120] >> Yeah. Today it's write coding and it's

[00:15:01.520] involved and not many people are going

[00:15:02.480] to do it but

[00:15:02.920] >> And you still have to make some design

[00:15:03.959] decisions, right? We were talking about

[00:15:05.240] like we take frames for example. Yeah.

[00:15:07.920] Yeah. But I kind of feel like this will

[00:15:10.160] just, uh, start to the barrier will just

[00:15:12.440] come down and it's just ephemeral

[00:15:14.240] software on your behalf and some kind of

[00:15:17.079] like claw is handling all the details

[00:15:18.920] for you but you're not involved. Claw

[00:15:20.520] has a Claw has a machine and it will

[00:15:22.400] figure it out and it's just presenting

[00:15:23.720] you UIs and you're like saying stuff,

[00:15:25.640] you know? Mhm.

[00:15:26.959] Why haven't you, um, I guess like pushed

[00:15:29.480] the boundaries of what you can do

[00:15:30.560] personally with claws? Like is it, you

[00:15:32.600] know, you're focusing on more important

[00:15:35.160] projects, auto research, etc. or, uh,

[00:15:38.280] you're climbing the hill to mastery or

[00:15:40.440] something else, right? Yeah, I just feel

[00:15:42.079] like I'm so distracted by everything so

[00:15:43.640] I spend I [laughter] spend like a week

[00:15:45.400] on the claw stuff and I I have more to

[00:15:47.600] do almost, um,

[00:15:49.360] but I will say that, um,

[00:15:50.280] >> It's like Jensen told us we're all just

[00:15:51.440] busier, unfortunately.

[00:15:53.720] >> Uh, I didn't really take advantage of a

[00:15:55.040] lot of like email and calendar and all

[00:15:57.240] this other stuff and I didn't really

[00:15:58.280] have access cuz I'm still a little bit

[00:15:59.920] like suspicious and it's still very new

[00:16:01.440] and rough around the edges. So I didn't

[00:16:03.160] want to give it like full access to my

[00:16:04.360] digital life yet and part of it is just

[00:16:06.079] the security, privacy and uh, just being

[00:16:08.480] very cautious in that in that realm.

[00:16:11.160] And, um, so some of it is like held back

[00:16:13.120] by that I would say. Yeah, maybe that's

[00:16:14.480] like the dominant dominant feature but

[00:16:16.560] some of it is also just I feel so

[00:16:17.760] distracted because I feel like I had a

[00:16:19.240] week of claw and then other stuff is

[00:16:20.880] happening and What was the, um, I mean

[00:16:23.360] you've talked about like being able to

[00:16:26.120] train or at least optimize a uh, a a

[00:16:28.800] model as a task you want to see agents

[00:16:30.680] do for a long time. Like what was the

[00:16:32.160] motivation behind auto research? Auto

[00:16:34.040] research, yeah. So I think like

[00:16:36.160] I had a tweet earlier where I kind of

[00:16:37.800] like said something along the lines of

[00:16:40.120] to get the most out of the tools that

[00:16:41.520] have become available now you have to

[00:16:43.200] remove yourself as the as the

[00:16:44.440] bottleneck. You can't be there to prompt

[00:16:46.480] the next thing. You're You need to take

[00:16:48.079] yourself outside. Um, you have to

[00:16:50.280] arrange things such that they're

[00:16:51.480] completely autonomous. And the more you

[00:16:53.560] you know, how can you maximize your

[00:16:54.560] token throughput and not be in the loop?

[00:16:56.120] This is the this is the goal. And so

[00:16:58.560] I kind of mentioned that the the name of

[00:16:59.800] the game now is to increase your

[00:17:00.760] leverage. Uh, I put in just very few

[00:17:02.880] tokens just once in a while and a huge

[00:17:04.520] amount of stuff happens on my behalf.

[00:17:06.560] And so auto research like I tweeted that

[00:17:08.280] and I think people liked it and whatnot

[00:17:09.800] but it

[00:17:10.959] they haven't like maybe worked through

[00:17:12.199] like the implications of that and for me

[00:17:13.760] auto research is an example of like an

[00:17:14.839] implication of that. Where it's like I

[00:17:16.920] don't want to be like the researcher in

[00:17:18.360] loop like looking at results, etc. Like

[00:17:20.600] I'm I'm holding the system back. So the

[00:17:23.160] question is how do I refactor all the

[00:17:24.839] abstractions so that I'm not I have to

[00:17:26.720] arrange it once and hit go. The name of

[00:17:28.679] the game is how can you get more agents

[00:17:30.760] running for longer periods of time

[00:17:32.000] without your involvement doing stuff on

[00:17:33.360] your behalf? And auto research is just,

[00:17:35.480] yeah, here's an objective, here's a

[00:17:36.880] metric, here's your boundaries of what

[00:17:38.400] you can and cannot do.

[00:17:39.800] And go.

[00:17:41.040] And, uh, yeah, it worked.

[00:17:43.360] >> at its effectiveness. Yeah, I I didn't

[00:17:45.280] expect, uh, it to work because so I have

[00:17:47.200] the project data chat, um,

[00:17:49.600] and fundamentally like I think a lot of

[00:17:50.720] people are very confused with my

[00:17:52.040] obsession for like training GPT-2 models

[00:17:53.840] and so on. But for me, uh, training GPT

[00:17:55.920] models and so on is just a little

[00:17:57.120] harness, a little playground for

[00:17:58.280] training LLMs. And fundamentally what

[00:18:00.000] I'm more interested in is like this idea

[00:18:01.480] of recursive self-improvement and to

[00:18:02.720] what extent you can actually have LLMs

[00:18:04.200] improving LLMs because I think all the

[00:18:06.000] frontier labs this is like the thing

[00:18:08.040] Mhm. uh, for obvious reasons and they're

[00:18:10.440] all trying to recursively self-improve

[00:18:12.040] roughly speaking. And so for me this is

[00:18:13.600] kind of like, um, a little playpen of

[00:18:15.640] that. Um, and I guess I like tuned Nan

[00:18:18.560] Chat already quite a bit by hand in the

[00:18:20.200] good old fashion way that I'm used to.

[00:18:21.320] Like I'm a researcher. I've done this

[00:18:22.360] for like, you know, two decades. I have

[00:18:23.560] some amount of like What is the opposite

[00:18:25.040] of hubris? Uh, yeah. [laughter]

[00:18:28.080] Earned confidence? Okay. I have like two

[00:18:30.760] decades of like, "Oh, I've trained this

[00:18:32.200] model like thousands of times. I've

[00:18:33.720] like,

[00:18:34.560] um, so I've done a bunch of experiments.

[00:18:36.080] I've done hyperparameter tuning. I've

[00:18:37.360] done all the things I'm very used to and

[00:18:38.600] I've done for two decades. Yeah. And

[00:18:39.919] I've gotten to a certain point and I

[00:18:41.919] thought it was like fairly well tuned

[00:18:43.640] and then I let auto research go for like

[00:18:45.400] overnight and it came back with like

[00:18:47.480] tunings that I didn't see. Mhm. And

[00:18:49.000] yeah, I did forget like the weight decay

[00:18:50.560] on the value embeddings and my Adam

[00:18:52.120] betas were not sufficiently tuned and

[00:18:54.520] these things just jointly interact. So

[00:18:56.080] like once you tune one thing the other

[00:18:57.360] things have to potentially change too.

[00:18:58.880] You know, I shouldn't be a bottleneck. I

[00:19:00.040] shouldn't be running these

[00:19:00.760] hyperparameter optimizations. I

[00:19:02.080] shouldn't be looking at the results.

[00:19:03.679] There's objective criteria in this case.

[00:19:05.400] Uh, so you just let you just have to

[00:19:06.840] arrange it so that it can just go

[00:19:08.000] forever. So that's a single sort of

[00:19:09.760] version of auto research of like a

[00:19:11.040] single loop trying to improve. And I was

[00:19:13.240] surprised that it, um, it found these

[00:19:15.320] things that I

[00:19:16.360] you know, the repo was already fairly

[00:19:17.520] well tuned and still found something.

[00:19:19.120] And that's just a single it's a single

[00:19:20.520] loop. Like these frontier labs they have

[00:19:22.880] GPU clusters of tens of thousands of

[00:19:25.159] them.

[00:19:26.159] And so it's very easy to imagine how you

[00:19:27.679] would basically get a lot of this

[00:19:29.720] automation on, um, smaller models. And

[00:19:32.240] fundamentally everything around like

[00:19:33.600] frontier level intelligence is about

[00:19:35.000] extrapolation and scaling loss. And so

[00:19:37.320] you basically do a ton of the

[00:19:38.120] exploration on the smaller models and

[00:19:40.200] then you try to, um, extrapolate out. So

[00:19:43.000] you're saying our research efforts are

[00:19:44.360] going to get more efficient. Like we're

[00:19:45.960] going to have better direction for when

[00:19:47.080] we scale as well if we can do this

[00:19:48.960] experimentation better.

[00:19:50.040] >> Yeah, I would say that like the most

[00:19:51.679] interesting project and probably what

[00:19:52.840] the frontier labs are working on is uh,

[00:19:54.600] Mhm. Yeah. you know, you experiment on

[00:19:55.880] the smaller models. You try to make it

[00:19:57.280] as autonomous as possible. Remove

[00:19:58.880] researchers

[00:19:59.973] >> [laughter]

[00:20:00.160] >> from the loop. They have way too much

[00:20:02.240] What is the What is the opposite

[00:20:04.400] of too much confidence? Yeah, yeah, they

[00:20:05.920] don't know. They shouldn't be touching

[00:20:07.160] any of this really. And so you have to

[00:20:08.560] like rewrite the whole thing because

[00:20:09.760] right now, I mean certainly they can

[00:20:11.320] contribute ideas. But okay, they

[00:20:13.680] shouldn't actually be enacting these

[00:20:15.000] ideas. There is a queue of ideas and

[00:20:17.360] there's maybe an automated scientist

[00:20:18.680] that comes up with ideas based on all

[00:20:20.320] the archive papers and GitHub repos and

[00:20:21.960] it funnels ideas in or researchers can

[00:20:24.160] contribute ideas, but it's a single

[00:20:25.680] queue and there is workers that pull

[00:20:27.840] items and they try them out. And

[00:20:30.080] whatever works just gets sort of put on

[00:20:31.920] the feature branch and maybe some people

[00:20:34.000] like

[00:20:35.240] monitor the feature branch and merge to

[00:20:37.200] the main branch sometimes. So

[00:20:39.720] yeah, just removing humans from all the

[00:20:42.080] processes and automating as much as

[00:20:43.440] possible and getting high token tokens

[00:20:45.080] per second throughputs and it does

[00:20:46.640] require rethinking of all the

[00:20:48.000] abstractions

[00:20:49.680] and everything has to be reshuffled. So

[00:20:52.880] yeah, I think it's very exciting. If we

[00:20:54.200] take one more recursive step here,

[00:20:57.520] when is the model going to write a

[00:20:58.640] better program MD than you?

[00:21:00.760] Yeah.

[00:21:01.960] Also program MD is like

[00:21:03.600] >> loop. Yeah, exactly.

[00:21:05.040] >> Yeah. So program MD is my crappy attempt

[00:21:07.920] at describing like how the auto

[00:21:10.080] researcher should work. Like oh, do this

[00:21:11.840] then do that and that and then try these

[00:21:13.680] kinds of ideas and then here's maybe

[00:21:15.200] some ideas like look at architecture,

[00:21:16.600] look at optimizer, etc. But I just came

[00:21:18.400] up with with this in markdown, right?

[00:21:19.960] >> Mhm.

[00:21:21.120] And so

[00:21:23.040] yeah, exactly.

[00:21:24.520] You want some kind of an auto research

[00:21:26.080] loop maybe that looks for

[00:21:28.440] You can imagine that different program

[00:21:29.720] that MDs would

[00:21:31.920] would give you different progress. So

[00:21:34.640] you basically every research

[00:21:35.800] organization is described by program MD.

[00:21:38.360] A research organization is a set of

[00:21:40.240] markdown files that describe all the

[00:21:41.640] roles and how the whole thing connects.

[00:21:43.560] And you can imagine having a better

[00:21:45.520] research organization. So maybe they do

[00:21:47.080] fewer stand-ups in the morning because

[00:21:48.520] they're useless. And this is all just

[00:21:50.040] code, right?

[00:21:51.480] And so you can So one organization can

[00:21:53.000] have fewer stand-ups, one organization

[00:21:54.480] can have more.

[00:21:56.080] One organization can be very

[00:21:57.280] risk-taking, one organization can be

[00:21:59.160] less. As you can definitely imagine that

[00:22:00.960] you have multiple research orgs

[00:22:02.960] and then they all have code. And once

[00:22:04.600] you have code, then you can imagine

[00:22:05.640] tuning the code. So 100% there's like

[00:22:07.400] the metal layer of it. Uh

[00:22:09.720] Did you see my text about my contest

[00:22:11.120] idea? My contest idea was

[00:22:14.440] like

[00:22:15.360] let people write different program MDs,

[00:22:18.280] right? And and so for same hardware,

[00:22:20.560] where do you get most improvement?

[00:22:22.240] >> Oh, I see. And then you can take all

[00:22:23.360] that data and then give it to the model

[00:22:25.520] and say write a better program MD.

[00:22:26.760] >> Yes, yes.

[00:22:28.040] Yeah, exactly.

[00:22:28.640] >> We're going to get something better.

[00:22:29.520] Like there's no way we don't, right?

[00:22:30.600] >> 100% look at

[00:22:32.320] where the improvements came from and

[00:22:34.040] like can I change the program MD such

[00:22:36.120] that more of these kinds of things would

[00:22:37.679] be done or like things that didn't work

[00:22:40.080] except

[00:22:41.560] you can 100% imagine doing that. So I

[00:22:43.280] think this is a great idea, but it's

[00:22:45.080] like

[00:22:45.960] you know, I think like you can sort of

[00:22:47.160] go one step at a time where you sort of

[00:22:48.640] have one process and then second process

[00:22:50.640] and then the next process and these are

[00:22:51.760] all layers of an onion.

[00:22:53.280] Like the LLM sort of part is now taken

[00:22:55.320] for granted. The agent part is now taken

[00:22:57.040] for granted. Now the claw-like entities

[00:22:59.000] are taken for granted and now you can

[00:23:00.400] have multiple of them and now you can

[00:23:01.760] have instructions to them and now you

[00:23:03.040] can have optimization over the

[00:23:04.280] instructions and it's just like a little

[00:23:06.040] too much, you know, but I mean this is

[00:23:07.880] why it gets to the psychosis is that

[00:23:09.160] this is like infinite and everything is

[00:23:10.600] scale issue and that's why I feel like

[00:23:12.720] Yeah, that's just coming back to This is

[00:23:14.560] why it's so insane. Okay, well, if

[00:23:16.476] [laughter] we're we're just trying to

[00:23:17.320] like diagnose the current moment and

[00:23:20.880] what is a relevant skill right now, what

[00:23:22.960] do you like what do you think is the

[00:23:24.240] implication that this

[00:23:26.280] that this is the loop we should be

[00:23:27.360] trying to achieve in different areas and

[00:23:29.400] then it works, right? Like you know,

[00:23:31.360] remove

[00:23:32.560] create the metric or create the ability

[00:23:34.560] for agents to continue working on it

[00:23:36.880] without you. Do we still have

[00:23:38.400] performance engineering? Like what

[00:23:40.520] Yeah, I mean so there's a few caveats

[00:23:42.080] that I would put on top of the LLM

[00:23:43.520] psychosis. So number one,

[00:23:45.160] this is extremely well suited to

[00:23:46.560] anything that has objective metrics that

[00:23:48.280] are easy to evaluate. So for example,

[00:23:49.880] like writing kernels for more efficient

[00:23:51.400] CUDA,

[00:23:52.440] you know, code for various parts of the

[00:23:54.360] model, etc. are a perfect fit because

[00:23:56.720] you have inefficient code and then you

[00:23:58.400] want efficient code that has the exact

[00:23:59.840] same behavior but it's much faster.

[00:24:02.120] Perfect fit. So a lot of things like

[00:24:04.600] like are perfect fit for auto research,

[00:24:06.520] but many things will not be. And so they

[00:24:08.560] it's just if you can't evaluate then you

[00:24:09.840] can't auto research it, right?

[00:24:12.200] So that's like caveat number one. And

[00:24:13.640] then maybe caveat number two I would say

[00:24:15.000] is you know, we're we're kind of talking

[00:24:16.480] about the next steps and we kind of see

[00:24:17.760] what the next steps are, but

[00:24:18.760] fundamentally the the whole thing still

[00:24:20.480] doesn't it still kind of like bursting

[00:24:22.240] at the seams a little bit and there's

[00:24:23.160] cracks and it doesn't fully work and if

[00:24:25.560] you kind of try to go too far ahead, the

[00:24:27.240] whole thing is actually net not useful

[00:24:29.320] if that makes sense.

[00:24:31.080] Because these models like still are not,

[00:24:32.760] you know, they've improved a lot, but

[00:24:34.080] they're still are like rough around the

[00:24:35.760] edges is maybe the way I would describe

[00:24:37.280] it. I simultaneously feel like I'm

[00:24:39.360] talking to an extremely brilliant PhD

[00:24:41.400] student who's been like a systems

[00:24:43.160] programmer for their entire life and a

[00:24:44.960] 10-year-old. And it's so weird because

[00:24:47.320] humans like there's like I feel like

[00:24:49.080] they're a lot more coupled like you have

[00:24:50.640] to you know, um Yes, you wouldn't you

[00:24:52.840] wouldn't encounter that combination.

[00:24:54.520] >> This jaggedness is really strange and

[00:24:56.440] humans have a lot less of that kind of

[00:24:57.760] jaggedness, although they definitely

[00:24:59.040] have some.

[00:24:59.967] >> [laughter]

[00:25:00.480] >> But humans have a lot more jaggedness.

[00:25:02.880] Uh sorry, the agents have a lot more

[00:25:04.080] jaggedness where

[00:25:05.720] sometimes like

[00:25:07.320] you know, I ask for functionality and it

[00:25:08.640] like comes back with something that's

[00:25:09.800] just like totally wrong and then we get

[00:25:11.679] into loops that are totally wrong and

[00:25:12.880] then I'm just I get so frustrated with

[00:25:14.280] the agents all the time still because

[00:25:16.040] you feel the power of it,

[00:25:17.840] but you also there's still like

[00:25:20.720] it does not say statistical things once

[00:25:21.920] in a while for me as well. I get very

[00:25:23.960] annoyed [clears throat] when

[00:25:26.400] I feel like the agent wasted a lot of

[00:25:29.360] compute on something it should have

[00:25:30.880] recognized was an obvious problem. Yeah.

[00:25:33.600] I think like some of the bigger things

[00:25:34.679] is like maybe what's under underneath it

[00:25:36.760] if I could hypothesize is fundamentally

[00:25:39.040] these models are trained via

[00:25:39.920] reinforcement learning. So they're

[00:25:41.000] actually struggling with the exact same

[00:25:42.000] thing we just talked about which is the

[00:25:43.640] labs can improve the models in anything

[00:25:45.760] that is verifiable or that

[00:25:47.127] [clears throat] has rewards. So did you

[00:25:48.800] write the program correctly and does it

[00:25:50.760] you do you the unit tests check out? Yes

[00:25:52.560] or no. But some of the things where

[00:25:54.120] they're struggling is like for example,

[00:25:55.320] I think they have a tough time with like

[00:25:57.360] nuance of maybe what I what I had in

[00:25:59.160] mind or what I intended and when to ask

[00:26:00.920] clarifying questions.

[00:26:02.640] Um

[00:26:03.240] or like what I Yeah, it's just um

[00:26:05.440] anything that feels softer is like

[00:26:07.080] worse. And so you're kind of like you're

[00:26:09.400] either on rails and you're part of the

[00:26:11.080] super intelligence circuits or you're

[00:26:12.920] not on rails and you're outside of the

[00:26:14.440] verifiable domains and suddenly

[00:26:15.640] everything kind of just like meanders.

[00:26:17.720] Like maybe another way to put it is if

[00:26:19.160] you go to if today if you go to like

[00:26:21.320] state-of-the-art model, ChatGPT and you

[00:26:22.840] ask it tell me a joke, um

[00:26:25.720] do you know what joke you're going to

[00:26:26.560] get? There's the joke. The joke? I do

[00:26:29.240] feel I I I can't tell you like the you

[00:26:31.320] know, standard form of it, but I do feel

[00:26:32.679] like ChatGPT has like three jokes.

[00:26:34.200] >> Yeah, yeah. So the the joke that

[00:26:36.200] apparently all the LLMs like love the

[00:26:37.640] most is why do scientists not trust

[00:26:40.600] atoms? Okay. Because they make

[00:26:42.440] everything up. Okay.

[00:26:44.000] >> They make everything up.

[00:26:45.720] So this is still

[00:26:46.840] >> emerge? So this is the joke you would

[00:26:48.760] get like three or four years ago and

[00:26:50.360] this is the joke you still get today.

[00:26:51.840] Okay.

[00:26:52.400] >> So even though the models have improved

[00:26:53.920] tremendously and if you give them an

[00:26:56.040] agentic task, they will just go for

[00:26:58.280] hours and move mountains for you. And

[00:27:00.920] then you ask for like a joke and it has

[00:27:02.600] a stupid joke. It's crappy joke from

[00:27:04.240] five years ago and it's because it's

[00:27:06.080] outside of the it's outside of the RL.

[00:27:08.840] It's outside of the reinforcement

[00:27:09.720] learning. It's outside of what's being

[00:27:10.720] improved. It's like and it's part of the

[00:27:13.000] jaggedness of like shouldn't you expect

[00:27:15.080] models as they get better to also have

[00:27:16.520] like better jokes or more diversity of

[00:27:18.080] them or it's just it's not being

[00:27:20.200] optimized and stuck. Do you

[00:27:23.920] think that that implies that we are not

[00:27:26.679] seeing like generalization in the sense

[00:27:29.240] of like broader intelligence of joke

[00:27:31.840] smartness being attached to code

[00:27:34.160] smartness? Yeah, I think there's some

[00:27:35.840] decoupling where some things are

[00:27:37.920] verifiable and some things are not and

[00:27:39.400] some things are optimized for

[00:27:40.400] arbitrarily by the labs depending on

[00:27:41.880] like what data went in and some things

[00:27:43.520] are not and um

[00:27:45.880] and

[00:27:46.360] >> But I mean the the premise there's a you

[00:27:48.840] know, premise from some research groups

[00:27:51.000] that if you're smarter at code

[00:27:53.160] generation or in these verifiable

[00:27:55.520] fields, you should be better at

[00:27:56.360] everything. And like the

[00:27:58.480] the joke situation suggests that that's

[00:28:00.000] not happening at all.

[00:28:01.320] Okay.

[00:28:01.720] >> Yeah, I don't think that's happening. I

[00:28:02.880] think

[00:28:03.840] I think maybe we're seeing like a little

[00:28:04.920] bit of that, but not like a satisfying

[00:28:06.280] amount.

[00:28:06.760] >> Yeah, that jaggedness exists in humans.

[00:28:09.640] You [laughter] can be very very good at

[00:28:11.160] math

[00:28:12.440] and still tell really bad jokes.

[00:28:13.920] >> Yeah, that's true. Yeah, but it just it

[00:28:15.400] still means that we're not getting like

[00:28:17.080] the story is that we're getting a lot of

[00:28:18.679] the intelligence and capabilities in all

[00:28:20.120] the domains of society like for free as

[00:28:22.760] we get better and better models and

[00:28:24.200] that's not like exactly fundamentally

[00:28:25.600] what's going on and there's some blind

[00:28:27.200] spots and some things are not being

[00:28:28.520] optimized for and this is all clustered

[00:28:30.720] up in these neural net opaque models,

[00:28:32.880] right? So you're either on rails of what

[00:28:35.240] it was trained for and everything is

[00:28:36.440] like you're going at speed of light or

[00:28:37.679] you're not.

[00:28:39.159] And so it's the jaggedness. So

[00:28:41.760] um

[00:28:42.480] So that's why I think like even though

[00:28:43.880] the the progression is obvious what

[00:28:45.960] should happen, you can't let it fully go

[00:28:49.000] there yet because it doesn't

[00:28:51.000] fully work or it's a scale issue and we

[00:28:52.960] just haven't like figured out how to use

[00:28:54.159] it. So you know, it's hard to tell. Can

[00:28:55.800] I ask a somewhat blasphemous question

[00:28:57.640] which is like if this jaggedness is

[00:29:00.320] persisting

[00:29:01.880] and it's all rolled up in a

[00:29:04.159] at least monolithic interface, right?

[00:29:05.840] But you know, single model.

[00:29:08.480] Does that make sense or do you should

[00:29:10.320] should it be unbundled into things that

[00:29:11.720] are can be optimized and improved

[00:29:13.720] against different domains of

[00:29:15.880] intelligence? Like unbundling the models

[00:29:17.960] into multiple experts in different

[00:29:19.280] areas, etc. More directly. Yeah. Um

[00:29:22.200] Instead of just MOE that we have no

[00:29:24.240] exposure to because that can be like

[00:29:25.919] confusing as a user from the outside

[00:29:28.159] which is like why is it so good at this,

[00:29:29.640] but not at this other thing? Yeah, I

[00:29:31.679] think currently my impression is the

[00:29:33.520] labs are trying to have a single sort of

[00:29:34.800] like monoculture of a model that is

[00:29:37.080] arbitrarily intelligent in all these

[00:29:39.280] different domains and they just stuff it

[00:29:40.880] into the parameters. I do think that we

[00:29:42.919] will we I do think we should expect more

[00:29:44.720] speciation in the

[00:29:46.840] intelligences.

[00:29:48.160] Um

[00:29:49.280] like, you know, the animal kingdom is

[00:29:51.000] extremely diverse in the brains that

[00:29:52.360] exist and there's lots of different

[00:29:53.880] niches of of nature and some animals

[00:29:56.680] have overdeveloped visual cortex or

[00:29:58.480] other part kind of parts and I think we

[00:30:00.880] we should be able to see more speciation

[00:30:03.040] and um you don't need like this oracle

[00:30:04.960] that knows everything. You can speciate

[00:30:06.520] it and then you put it on a specific

[00:30:07.920] task and we should be seeing some of

[00:30:09.120] that because you should be able to have

[00:30:10.680] like much smaller models that still have

[00:30:11.960] the cognitive core like they're still

[00:30:13.320] competent but then they specialize and

[00:30:15.200] then um and then they they can become

[00:30:17.760] more efficient in terms of latency or

[00:30:19.680] throughput on

[00:30:21.000] specific tasks that you really care

[00:30:22.120] about. Like if you're a mathematician

[00:30:23.360] working in Lean, I saw for example

[00:30:24.960] there's a few releases that really like

[00:30:26.280] target that as a domain. Um

[00:30:28.560] uh so there's a probably going to be a

[00:30:29.960] few examples like that where the

[00:30:31.360] unbundling kind of makes sense. One

[00:30:33.320] question I have is whether or not the

[00:30:36.200] capacity constraint on available compute

[00:30:39.000] infrastructure Mhm. drives more of this

[00:30:41.320] because efficiency Yeah. actually

[00:30:43.160] matters more. Yeah.

[00:30:45.000] Your if you

[00:30:47.400] financing aside, though financing's

[00:30:49.240] involved in all of this. If you have

[00:30:50.560] access to full compute for anything you

[00:30:52.720] do like even one single model, right?

[00:30:55.560] But if you actually feel pressure where

[00:30:57.400] you're like I can't serve

[00:30:59.560] >> Mhm. um

[00:31:01.240] model of massive size for every use

[00:31:03.160] case.

[00:31:03.640] >> Mhm. Like do you think that leads to any

[00:31:05.240] speciation? Does that question make

[00:31:06.760] sense to you? The question makes sense

[00:31:08.280] and I guess like what I'm what I'm what

[00:31:10.200] I what I'm struggling with is I don't

[00:31:11.840] think we've seen too much speciation

[00:31:13.120] just yet, right? No. Uh we're seeing a

[00:31:15.240] monoculture of models. Yeah. So um And

[00:31:17.560] there's like clearly pressure for like

[00:31:19.200] make a good code model, put it back in

[00:31:20.720] the main, merge again. Yeah.

[00:31:23.040] >> Um

[00:31:25.720] even though there already is pressure on

[00:31:27.240] the models. Mhm. I guess perhaps I I

[00:31:29.480] feel like there's a lot of very

[00:31:30.640] short-term supply crunch and like maybe

[00:31:33.160] that causes more speciation now.

[00:31:35.520] Yeah, I think fundamentally like the

[00:31:37.960] the the labs are serving a model and

[00:31:39.880] they don't really know what the end user

[00:31:41.760] is going to be asking about. So maybe

[00:31:43.880] that's like some part of it because they

[00:31:45.200] kind of have to multitask over all the

[00:31:46.360] possible things they could be asked. But

[00:31:48.000] I think if you're coming to a business

[00:31:49.120] and maybe partnering on some specific

[00:31:50.720] problems you care about then maybe you

[00:31:52.360] would see that there. Um or there would

[00:31:54.679] be some very high-value applications

[00:31:56.320] that are like more niche. Um

[00:31:58.440] But but I think right now they're kind

[00:32:00.320] of like going after the totality of

[00:32:01.679] what's available. I don't think that the

[00:32:03.240] science of manipulating the brains is

[00:32:05.880] like fully developed yet partly. What do

[00:32:07.600] you mean manipulating? So like so

[00:32:09.600] fine-tuning without losing capabilities

[00:32:11.440] as an example. And I we don't have these

[00:32:13.080] primitives for actually like working

[00:32:14.240] with the intelligences in ways other

[00:32:15.920] than just context windows. Our context

[00:32:17.520] windows kind of just just work and it's

[00:32:19.440] very cheap to manipulate etc. And this

[00:32:20.840] is how we're getting some of the

[00:32:21.600] customization etc. Uh but I think if it

[00:32:23.920] was I think it's a it's a bit more of a

[00:32:26.480] developing science of how you like more

[00:32:27.880] deeply adjust the models, how you have

[00:32:29.920] continual learning maybe or how you

[00:32:32.480] um how you fine-tune in a certain area,

[00:32:34.040] how you get better in a certain area or

[00:32:35.400] like how you actually touch the weights

[00:32:36.760] not just the context windows. And so

[00:32:38.360] it's a lot more

[00:32:39.679] tricky I would say to touch the weights

[00:32:41.160] than just the context windows uh because

[00:32:43.040] you're actually fundamentally changing

[00:32:44.080] the full model and potentially its

[00:32:45.440] intelligence. And so um

[00:32:48.000] so maybe it's just like not a fully

[00:32:49.240] developed science if that makes sense of

[00:32:50.520] speciation. And it also has to be like

[00:32:53.080] cheap enough Yeah. for that speciation

[00:32:55.280] to be worthwhile in these given

[00:32:57.520] >> contexts. Can I ask a question about

[00:32:59.960] like an extension to auto research that

[00:33:02.320] you described in terms of open ground?

[00:33:04.640] You say okay, well, you know, we have

[00:33:06.200] this thing. Um we need more

[00:33:08.760] collaboration surface around it

[00:33:10.520] essentially for people to contribute

[00:33:13.440] to research overall. Can you talk about

[00:33:15.280] that?

[00:33:15.679] >> Yeah, so we talked about auto research

[00:33:16.760] has a single thread of like I'm going to

[00:33:18.080] try stuff in a loop but fundamentally

[00:33:20.720] the parallelization of this is like the

[00:33:22.080] interesting component.

[00:33:23.960] And I guess I was trying to like play

[00:33:25.000] around with a few ideas but I don't have

[00:33:26.720] anything that like clicks as simply as

[00:33:28.560] like I don't have something I'm like

[00:33:29.720] super happy with just yet but it's

[00:33:30.800] something I'm like working on the side

[00:33:32.600] when I'm not working on my claw.

[00:33:34.840] Um

[00:33:35.800] so I think like one issue is if you have

[00:33:38.040] a bunch of nodes

[00:33:40.080] of parallelization available to then

[00:33:41.800] it's very easy to just have multiple

[00:33:43.160] auto researchers talking through a

[00:33:45.280] a common system or something like that.

[00:33:46.880] What I was more interested in is how you

[00:33:48.040] can have an untrusted pool of workers

[00:33:49.840] out there on the internet. Mhm. So for

[00:33:51.520] example in auto research

[00:33:53.679] you're just trying to find um

[00:33:56.520] the piece of code that trains a model to

[00:33:58.160] a very low validation loss.

[00:34:00.640] If anyone gives you a candidate commit,

[00:34:02.720] it's very easy to verify that that

[00:34:04.360] commit is correct is good. Like they

[00:34:06.679] someone could claim from the internet

[00:34:07.840] that this piece of code will optimize

[00:34:09.879] much better and give you much better

[00:34:10.919] performance. You could just check. Yeah.

[00:34:12.960] But probably a lot of work goes into

[00:34:14.960] that checking.

[00:34:16.000] But fundamentally they could lie and

[00:34:17.600] etc. So you're basically dealing with a

[00:34:19.399] similar kind of it's almost actually

[00:34:20.640] like looks a little bit like my my

[00:34:22.240] designs that incorporate an untrusted

[00:34:23.840] pool of workers

[00:34:25.120] actually look a little bit more like a

[00:34:26.480] blockchain a little bit uh because

[00:34:28.640] instead of blocks you have commits and

[00:34:31.159] these commits can build on each other

[00:34:32.200] and they contain like changes to the

[00:34:33.520] code as you're improving it. Um and uh

[00:34:36.960] the proof of work is basically doing

[00:34:38.320] tons of experimentation to find the

[00:34:39.560] commits that work.

[00:34:40.960] Um and that's hard

[00:34:42.960] and then the reward is just being on the

[00:34:44.280] leaderboard right now. There's no

[00:34:45.879] monetary reward whatsoever.

[00:34:47.679] Uh but I don't want to push the analogy

[00:34:48.960] too far but it fundamentally has this

[00:34:50.480] issue where

[00:34:51.600] you a huge amount of search goes into it

[00:34:53.320] but it's very cheap to verify that a

[00:34:55.320] candidate solution is indeed good

[00:34:57.040] because you can just train a single you

[00:34:58.720] know, someone had to try 10,000 ideas

[00:35:00.240] but

[00:35:01.040] you just have to check that the thing

[00:35:02.040] that they produced actually works

[00:35:03.520] because the 99,000 of them didn't work,

[00:35:05.720] you know? Um and so basically long story

[00:35:08.920] short is like you have to come up with a

[00:35:10.120] system where an untrusted pool of

[00:35:12.800] workers can collaborate with a trusted

[00:35:14.880] pool of workers that do the

[00:35:16.760] verification.

[00:35:18.000] And the whole thing is kind of like

[00:35:19.359] asynchronous and works and

[00:35:22.080] and so on and it's it's like safe from a

[00:35:24.560] security perspective because if anyone

[00:35:25.920] sends you arbitrary code and you're

[00:35:27.080] going to run it, that is very sketchy

[00:35:28.640] and dodgy. So um

[00:35:30.880] but fundamentally it should be totally

[00:35:31.960] possible. So you're familiar with

[00:35:32.920] projects like SETI@home and

[00:35:34.120] Folding@home. All of these problems have

[00:35:35.880] a similar kind of setup. So Folding@home

[00:35:38.080] you're folding a protein

[00:35:39.920] and it's very hard to find a

[00:35:40.800] configuration that is low energy. But if

[00:35:42.440] someone finds a configuration that they

[00:35:43.760] value to be low energy, that's perfect.

[00:35:45.280] You can just use it. You can easily

[00:35:46.280] verify it.

[00:35:47.320] So a lot of things have this property

[00:35:48.520] that you know, very expensive to come up

[00:35:50.120] with but very cheap to verify. And so in

[00:35:52.680] all those cases things like Folding@home

[00:35:54.560] or SETI@home or auto research at home

[00:35:57.080] will be good fits. And so um long story

[00:36:00.120] short

[00:36:01.160] a swarm of agents on the internet could

[00:36:03.160] collaborate to improve LLMs and could

[00:36:05.800] potentially even like run circles around

[00:36:07.440] frontier labs. Like who knows, you know?

[00:36:09.600] Um

[00:36:10.840] yeah, like maybe that's even possible.

[00:36:12.200] Like frontier labs have a huge amount of

[00:36:13.800] trusted compute but the earth is much

[00:36:16.440] bigger and has huge amount of untrusted

[00:36:18.000] compute. But if you put systems in check

[00:36:20.560] systems in place that you know, deal

[00:36:22.320] with this then maybe it is possible that

[00:36:24.720] the swarm out there could could come up

[00:36:26.760] with with better with better solutions.

[00:36:29.560] And people kind of like contribute

[00:36:30.760] cycles um

[00:36:32.480] to to a thing that they care about. And

[00:36:34.520] so sorry to so the last thought is

[00:36:36.680] uh lots of companies or whatnot they

[00:36:37.960] could maybe have like their own things

[00:36:39.520] that they care about and you if you have

[00:36:41.400] compute capacity you could contribute to

[00:36:43.280] different kind of auto research tracks.

[00:36:44.920] Like maybe you care about certain you

[00:36:46.600] know, like you care about like cancer or

[00:36:48.320] something like that of certain type. You

[00:36:49.760] don't have to just donate money to an

[00:36:50.760] institution. You actually could like

[00:36:52.359] purchase compute and then you could join

[00:36:54.440] the auto research swarm for that

[00:36:55.920] project, you know? Uh so if everything

[00:36:58.680] is rebundled into auto researchers then

[00:37:00.680] compute becomes the thing that you're

[00:37:01.680] contributing to the pool. Yeah. That's

[00:37:03.680] very inspiring and it's also

[00:37:04.960] interesting. Like I don't I don't know

[00:37:06.400] how far this goes but it is interesting

[00:37:08.680] that at least some audience of people

[00:37:11.440] you know, here in Silicon Valley or

[00:37:13.120] lining up at you know, retail stores in

[00:37:15.480] China have discovered that like having

[00:37:18.080] access to personal compute is

[00:37:19.680] interesting again.

[00:37:20.480] >> Yeah. Right? So maybe they're really

[00:37:21.880] motivated to do that for their claws and

[00:37:23.920] then they can contribute to auto

[00:37:25.440] research.

[00:37:25.960] >> almost like dollars the thing everyone

[00:37:27.600] cares about but is flop the thing that

[00:37:29.800] actually everyone cares about in the

[00:37:31.120] future? Like is there going to be like a

[00:37:32.359] flipening almost of like what's the

[00:37:34.040] thing that you care about? Like right

[00:37:35.160] now for example it's really hard to get

[00:37:36.320] compute even if you have money. Yeah.

[00:37:38.680] So actually it almost seems like the

[00:37:40.040] flop is like dominant

[00:37:41.741] >> [laughter]

[00:37:42.280] >> in a certain sense. Um

[00:37:44.440] Yeah, so so maybe that's kind of like

[00:37:46.120] that. Kind of like that. Like how much

[00:37:47.920] how many flops do you control instead of

[00:37:49.240] like what wealth you control? I don't

[00:37:51.040] actually think that's true but it's kind

[00:37:52.200] of interesting to think about. The last

[00:37:54.200] thing you released was like a little bit

[00:37:55.720] of jobs data analysis. Is that right?

[00:37:58.520] What

[00:37:59.800] and might have touched a nerve even

[00:38:01.440] though you're just like visualizing some

[00:38:02.760] public data.

[00:38:03.440] >> Yeah. Uh what was you know, what were

[00:38:05.359] you curious about? Yeah, I guess I was

[00:38:06.840] curious to um

[00:38:09.080] I mean everyone is like really it's

[00:38:10.600] everyone is really thinking about the

[00:38:11.520] impacts of AI on the job market and

[00:38:13.320] what's going to look like. So I was just

[00:38:15.200] interested to take a look like what does

[00:38:16.440] the job market look like? Where are the

[00:38:17.680] different roles um

[00:38:19.560] and how many people are in different

[00:38:20.640] professions? And I was like really just

[00:38:22.080] interested to like look through

[00:38:24.040] the individual cases and try to think

[00:38:25.560] myself about like you know, with these

[00:38:27.600] AIs and how they're likely to evolve

[00:38:29.120] like

[00:38:30.400] are these going to be tools that people

[00:38:31.680] are using? Are these going to be

[00:38:33.080] displacing tools for these professions?

[00:38:36.000] And like what are the current

[00:38:37.280] professions and how are they going to

[00:38:38.720] change? Are they going to grow or uh

[00:38:40.840] adjust to a large extent or like what

[00:38:42.359] could be new professions? So it's really

[00:38:43.800] just like a way to fuel my own chain of

[00:38:45.280] thought about the industry I suppose.

[00:38:47.240] Mhm. Um and so

[00:38:49.920] yeah, the jobs data basically is just a

[00:38:51.200] Bureau of Labor Statistics. They

[00:38:53.080] actually have um percent outlook for

[00:38:55.880] each profession about how much it's

[00:38:57.400] expected to grow over the next I think

[00:38:58.880] almost a decade. Uh yeah, I think it's a

[00:39:00.720] decade but it was made in 2024. Mhm. We

[00:39:02.800] need a lot of health care workers. Yeah.

[00:39:04.920] So so they've already made those

[00:39:06.200] projections and I'm not sure actually

[00:39:07.680] 100% what the methodology was that they

[00:39:09.640] they put into their projections. Um I

[00:39:11.920] guess I was interested to color things

[00:39:13.600] by like if people think that what's like

[00:39:15.640] primarily being

[00:39:17.120] developed now is this kind of like more

[00:39:18.440] digital AI

[00:39:20.120] that is kind of like almost like these

[00:39:21.320] ghosts or spirit entities that can like

[00:39:23.160] interact in the digital world and

[00:39:25.400] manipulate a lot of like digital

[00:39:26.520] information and they currently don't

[00:39:28.000] really have a physical embodiment or

[00:39:29.720] presence. And the physical stuff is

[00:39:31.160] probably going to go slightly slower

[00:39:32.400] because you're manipulating atoms. So

[00:39:34.160] flipping flipping bits and

[00:39:36.000] and the ability to copy-paste digital

[00:39:37.880] information is like makes everything a

[00:39:39.560] million times faster than accelerating

[00:39:41.520] matter, you know, so

[00:39:43.320] Um so energetically, I just think we're

[00:39:45.240] going to see a huge amount of activity

[00:39:46.640] in the digital space, huge amount of

[00:39:48.080] rewriting, huge amount of activity,

[00:39:50.120] boiling soup. And I think the we're

[00:39:52.560] going to see something that in the

[00:39:53.880] digital space goes at the speed of light

[00:39:55.160] compared to I think what's going to

[00:39:56.160] happen in the physical world to some

[00:39:57.360] extent. If it would be the

[00:39:58.960] extrapolation. And so I think like

[00:40:01.257] >> [clears throat]

[00:40:01.800] >> there's currently kind of like I think

[00:40:03.520] overhang where there can be like a lot

[00:40:06.040] of unhubbling almost potentially of like

[00:40:08.120] a lot of digital information processing

[00:40:09.880] that used to be done by computers and

[00:40:11.640] people. And now with AIs there's like a

[00:40:13.200] third kind of manipulator of digital

[00:40:14.560] information. There's going to be a lot

[00:40:15.680] of refactoring in those in those

[00:40:18.000] disciplines.

[00:40:19.080] Um but the physical world is actually

[00:40:21.000] going to be like I think

[00:40:22.840] behind that by some amount of time. And

[00:40:24.960] so I think what's really fascinating to

[00:40:25.880] me is like

[00:40:27.640] So that's why I was highlighting the the

[00:40:29.040] professions that fundamentally

[00:40:30.480] manipulate digital information. This is

[00:40:31.800] work you could do from your home, etc.

[00:40:33.920] Uh because I feel like those will be

[00:40:35.200] like things will change. And it doesn't

[00:40:36.720] mean that there's going to be less of

[00:40:38.120] those jobs or more of those jobs because

[00:40:39.640] it does has to do with like demand

[00:40:40.800] elasticity and many other factors. But

[00:40:42.720] things will change in these professions

[00:40:44.240] because of these new tools and um

[00:40:46.840] because of this upgrade to the nervous

[00:40:48.120] system of the human superorganism

[00:40:50.383] >> [laughter]

[00:40:50.640] >> if you want to think about it that way.

[00:40:52.040] Given the look you had at the data, do

[00:40:53.640] you have either any observations or um

[00:40:57.120] uh guidance for people facing the job

[00:40:59.520] market or thinking about what to study

[00:41:01.120] now or what skills to develop? I mean we

[00:41:03.120] can all go get like I'm very thankful

[00:41:05.720] that I have to like meet people for my

[00:41:06.880] job right now.

[00:41:07.840] >> Yeah.

[00:41:08.068] >> [laughter]

[00:41:08.120] >> Yeah, more physical. Yeah. Could you do

[00:41:10.160] your work from home though? I could.

[00:41:13.080] I think there are relationship parts of

[00:41:14.320] it that are hard, but most of it I

[00:41:15.800] could. Yeah. I think it's really hard to

[00:41:17.280] tell because again like the job market

[00:41:18.480] is extremely diverse. I think the

[00:41:19.800] answers will probably vary, but uh to a

[00:41:21.800] large extent like these tools are

[00:41:22.960] extremely new, extremely powerful. And

[00:41:24.480] so just being you know, just trying to

[00:41:26.040] keep up with it is like the first thing.

[00:41:28.680] Um

[00:41:29.520] and um

[00:41:31.360] yeah, because I think a lot of people

[00:41:32.320] kind of like dismiss it or Or they're

[00:41:34.080] afraid of it. Or they're afraid of it,

[00:41:35.480] etc. As which is totally understandable,

[00:41:37.480] of course. Yeah, I think like um

[00:41:39.520] it's fundamentally an empowering tool at

[00:41:41.000] the moment. Um and these jobs are

[00:41:43.520] bundles of tasks. And some of these

[00:41:44.800] tasks can go a lot faster. And so people

[00:41:46.240] should think of it as primarily a tool

[00:41:47.360] that it is right now.

[00:41:48.720] Um and I think the long-term future of

[00:41:50.680] that is uncertain. Yeah, it's kind of

[00:41:52.520] really hard to forecast, to be honest.

[00:41:54.480] And like I'm not professionally like

[00:41:56.040] doing that really. And I think this is a

[00:41:57.360] job of like economists to do properly.

[00:41:59.720] You are an engineer though. And like one

[00:42:02.200] thing I thought was interesting is that

[00:42:03.520] like

[00:42:04.440] the demand for engineering jobs

[00:42:06.840] is continuing to increase.

[00:42:08.160] >> Yeah. Um I I can't tell if that's like a

[00:42:10.360] temporary phenomenon. I'm not sure how I

[00:42:11.720] feel about it. Yeah, do you know? Yeah,

[00:42:13.360] that's like the demand elasticity almost

[00:42:14.840] like uh software was scarce, right? And

[00:42:17.520] so the reason we don't have more demand

[00:42:19.320] for software is just there's its

[00:42:20.640] scarcity and it's too expensive.

[00:42:22.320] >> So if the barrier comes down, then

[00:42:23.520] actually you have the Jevons paradox,

[00:42:25.360] which is like you know, you actually the

[00:42:26.520] demand for software actually goes up.

[00:42:27.920] It's cheaper and there's more More

[00:42:29.440] powerful, yeah. The the classical

[00:42:31.320] example of this always is the ATMs and

[00:42:33.520] the bank tellers

[00:42:34.880] uh because there was a lot of like fear

[00:42:36.480] that um ATMs and computers basically uh

[00:42:39.800] would displace tellers. But what

[00:42:41.440] happened is they made like the cost of

[00:42:42.960] operation of

[00:42:44.440] of a bank branch much cheaper. And so

[00:42:46.680] there are more bank branches, so there

[00:42:47.720] are more tellers. It's like the

[00:42:49.440] canonical example people cite. Uh but

[00:42:51.400] basically it's just Jevons paradox. Like

[00:42:52.800] something becomes cheaper, so there's

[00:42:55.200] a lot of unlocked demand for it. Uh so I

[00:42:57.640] do think that that's probably I do have

[00:42:59.760] like cautiously optimistic view of this

[00:43:01.480] in software engineering

[00:43:02.920] where I do think um it does seem to me

[00:43:05.080] like the demand for software will be

[00:43:06.120] extremely large. Um and it's just become

[00:43:08.640] a lot cheaper. And um

[00:43:11.840] so I do think that for quite some time

[00:43:14.480] um

[00:43:15.720] it's very hard to forecast, but it does

[00:43:17.400] seem to me like right now at least

[00:43:18.400] locally there's going to be more demand

[00:43:19.720] for software.

[00:43:20.840] Um because software is amazing. It's

[00:43:22.200] like you know, digital information

[00:43:23.160] processing. You're not forced to use

[00:43:25.000] like arbitrary tools that were given to

[00:43:26.320] you. They're imperfect in various ways.

[00:43:27.760] You're not forced to subscribe to what

[00:43:29.520] exists. Code is now ephemeral and it can

[00:43:31.920] change and it can be modified.

[00:43:33.880] Um

[00:43:34.480] and so I think there's going to be a lot

[00:43:35.840] of activity in the digital space to like

[00:43:38.200] rewire everything in a certain sense.

[00:43:40.080] And I think it's going to create a lot

[00:43:40.920] of demand for for this kind of stuff. I

[00:43:43.000] think long-term um yeah, obviously even

[00:43:45.600] with auto research like OpenAI or or you

[00:43:48.200] know, Anthropic or these other labs like

[00:43:50.200] they're employing what like a thousand

[00:43:51.800] something researchers, right?

[00:43:53.120] >> Mhm. These researchers are basically

[00:43:54.520] like glorified auto like you know.

[00:43:57.060] >> [laughter]

[00:43:58.080] >> They're like automating themselves away

[00:43:59.400] like actively and this is like the thing

[00:44:00.760] they're all trying to do. Yeah. I

[00:44:02.840] like I went around um Some of those

[00:44:04.520] researchers also fear that feel the

[00:44:06.040] psychosis, right? Because they can it's

[00:44:07.960] working, right? And and so they're like

[00:44:10.480] it's over for me, too. I did spend a

[00:44:12.040] bunch of time going around OpenAI and I

[00:44:13.359] was like, you guys realize if we're

[00:44:14.480] successful like we're all out of job

[00:44:15.960] like

[00:44:16.920] like this is just going to we're just

[00:44:17.760] building automation for Sam or something

[00:44:19.640] like that. Like I or the board or I'm

[00:44:21.640] not sure, but like uh they're just

[00:44:23.840] building all this automation for yeah,

[00:44:25.800] the board or the CEO or something like

[00:44:27.240] that. And we're all out of our job and

[00:44:29.320] maybe

[00:44:30.160] contributing on the side. And so

[00:44:32.840] yeah, it's kind of like unnerving from

[00:44:34.520] that perspective. Is it okay if I ask

[00:44:36.200] you Noam's question? Mhm. You know, you

[00:44:38.320] could be doing that, right? Auto

[00:44:40.280] researching with a lot of compute scale

[00:44:42.160] and a bunch of colleagues at one of the

[00:44:43.400] frontier [clears throat] labs. Like why

[00:44:44.480] not? Well, I was there for a while,

[00:44:46.160] right? Like and I did reenter. So to

[00:44:48.400] some extent I agree and I think that

[00:44:49.800] there are many ways to slice this

[00:44:50.760] question. It's very loaded question a

[00:44:52.240] little bit. Um I will say that I feel

[00:44:54.800] very good about like what people can

[00:44:56.200] contribute and their impact outside of

[00:44:58.720] the frontier labs, obviously. Not in the

[00:45:00.600] industry, but also in like more like

[00:45:02.160] ecosystem level roles. Um so your role

[00:45:05.120] for example is more like ecosystem

[00:45:06.240] level. My role currently is also kind of

[00:45:07.640] more on ecosystem level. And I feel very

[00:45:09.240] good about like impact that people can

[00:45:10.480] have in those kinds of roles. I think

[00:45:12.480] conversely there's there are definite

[00:45:14.120] problems in my mind for um uh for

[00:45:17.200] basically aligning yourself way too much

[00:45:18.560] with the frontier labs, too. So

[00:45:20.080] fundamentally I mean you're you have a

[00:45:21.640] huge amount of financial incentive to uh

[00:45:23.960] with these frontier labs. And by your

[00:45:25.400] own admission, the uh the AIs are going

[00:45:27.680] to like really change humanity and

[00:45:29.400] society in very dramatic ways. And here

[00:45:31.520] you are basically like building the

[00:45:33.359] technology and benefiting from it like

[00:45:35.160] it and being like very allied to it

[00:45:36.560] through financial means. Like this was

[00:45:38.320] the conundrum that was in at the heart

[00:45:40.480] of you know, how OpenAI was started in

[00:45:42.480] the beginning. Like this was the

[00:45:43.400] conundrum that we were trying to solve.

[00:45:44.840] Mhm. Um and so you know, that

[00:45:47.800] so it's kind of um It's still not

[00:45:49.800] resolved.

[00:45:50.520] >> is still not like fully resolved. So

[00:45:51.800] that's number one. You're you're not a

[00:45:53.480] completely free agent and you can't

[00:45:54.720] actually like be part of that

[00:45:55.640] conversation in a fully autonomous um

[00:45:58.200] free way. Like if you're inside one of

[00:45:59.920] the frontier labs. Like there's some

[00:46:01.400] things that you can't say. Uh and

[00:46:03.080] conversely there are some things that

[00:46:04.240] the organization wants you to say. And

[00:46:06.240] you know, they're not going to twist

[00:46:07.080] your arm, but

[00:46:08.560] you feel the pressure of like what you

[00:46:09.960] should be saying,

[00:46:11.400] you know, cuz like obviously

[00:46:13.956] >> [laughter]

[00:46:14.720] >> otherwise it's like really awkward

[00:46:15.840] conversations,

[00:46:17.440] uh strange side eyes, like what are you

[00:46:18.760] doing, you know, like so you can't like

[00:46:20.600] really be an independent agent. And I I

[00:46:22.400] feel like a bit more a lot like aligned

[00:46:24.400] with humanity in a certain sense outside

[00:46:25.880] of the frontier lab because

[00:46:27.720] I don't I'm not subject to those

[00:46:28.960] pressures almost, right? And I can say

[00:46:30.359] whatever I want or Yeah, I would say in

[00:46:31.960] the frontier labs like um

[00:46:34.320] you can have like

[00:46:35.720] impact there of course as well. So

[00:46:37.720] but there's many researchers and maybe

[00:46:39.160] you're one of them, maybe your ideas are

[00:46:40.320] really good, etc. Maybe there's a lot of

[00:46:41.920] decision-making to do and you want to be

[00:46:43.359] in a position where you are in the room

[00:46:44.560] with those conversations when they come

[00:46:45.680] up. I do think that currently the stakes

[00:46:47.200] are like overall fairly low and so

[00:46:49.000] everything is kind of like nice. But

[00:46:50.840] ultimately in the end of the day like

[00:46:52.120] when the stakes are really high, etc. If

[00:46:53.840] you're an employee at an organization, I

[00:46:55.280] don't actually know how much sway you're

[00:46:56.520] going to have on your organization what

[00:46:57.840] it's going to do. Like fundamentally at

[00:46:59.080] the end of the day um

[00:47:01.000] uh it's uh you're not like really in

[00:47:03.320] charge. Like you're in the room and

[00:47:04.359] you're contributing ideas, but you're

[00:47:05.720] not like really in charge of that entity

[00:47:07.080] that you're that you're part of. So

[00:47:08.600] those are like some sources of

[00:47:09.640] misalignment, I think to some extent. I

[00:47:11.480] will say that like in one way I do agree

[00:47:13.640] a lot with that sentiment that um I do

[00:47:16.480] feel like in the

[00:47:17.760] like the labs for better or worse

[00:47:18.880] they're opaque and a lot of work is

[00:47:20.200] there. And they're kind of like at the

[00:47:21.920] edge of capability and what's possible.

[00:47:23.320] And they're working on what's coming

[00:47:24.600] down the line. And I think if you're

[00:47:26.120] outside of that frontier lab, your your

[00:47:28.680] judgment fundamentally will start to

[00:47:29.920] drift because you're not part of the

[00:47:32.160] you know,

[00:47:33.080] what's coming down the line. And so I

[00:47:34.680] feel like my judgment will inevitably

[00:47:36.120] start to drift as well. And I won't

[00:47:38.000] actually have an understanding of how

[00:47:39.000] these systems actually work under the

[00:47:40.200] hood. That's an opaque system.

[00:47:42.080] I won't have a a good understanding of

[00:47:43.800] how it's going to develop and etc. And

[00:47:45.720] so I do think that in that sense I agree

[00:47:48.040] and something I'm nervous about. I think

[00:47:49.520] it's worth basically

[00:47:51.400] being in touch with what's actually

[00:47:52.480] happening and actually being in a

[00:47:53.640] frontier lab. And if if some of the

[00:47:55.359] frontier labs would have me come for you

[00:47:57.240] know, some amount of time and do really

[00:47:58.640] good work for them and then maybe come

[00:48:00.440] and hang out.

[00:48:00.800] >> looking for a job. This is super

[00:48:01.920] exciting. [laughter]

[00:48:03.520] Then I think that's maybe a good setup

[00:48:05.080] because I kind of feel like it's kind of

[00:48:06.440] um

[00:48:07.000] you know,

[00:48:08.680] maybe that's like one way Mhm. uh to to

[00:48:10.760] actually be connected to what's actually

[00:48:12.359] happening, but also not feel like you're

[00:48:13.680] necessarily fully controlled by Yeah. by

[00:48:15.840] those entities. So I think

[00:48:17.560] honestly in my mind like

[00:48:19.240] Noam can probably get do extremely good

[00:48:21.080] work at at OAI, but also I think his

[00:48:23.120] most impactful work could very well be

[00:48:25.200] outside of OpenAI. Noam, that's a call

[00:48:27.040] to be an independent researcher with

[00:48:28.720] auto [laughter] research.

[00:48:30.320] Yeah, there's many things to do on the

[00:48:31.200] outside and it's it's a

[00:48:33.359] and I think ultimately I think the ideal

[00:48:35.040] solution maybe is like yeah, going back

[00:48:36.880] and forth

[00:48:38.000] or um

[00:48:39.800] yeah, and I think fundamentally you can

[00:48:40.880] have a really amazing impact in both

[00:48:42.200] places. So very complicated I don't

[00:48:43.880] know. Like it's a very loaded question a

[00:48:45.400] little bit, but I mean I joined the

[00:48:46.960] frontier lab and I'm outside. And then

[00:48:48.640] maybe in the future I'll want to join

[00:48:50.000] again. And I think um

[00:48:52.880] uh that's kind of like how I look at it.

[00:48:54.440] One question related to what visibility

[00:48:57.120] to does the world or the AI ecosystem

[00:49:00.080] have into

[00:49:01.760] the frontier is like how how close open

[00:49:04.720] source is to the frontier. Mhm. Um and

[00:49:07.040] how sustainable that is. I I think Yeah.

[00:49:09.840] I think it is quite surprising. The

[00:49:12.640] entire sequence of events actually from

[00:49:14.240] like having a handful of Chinese models

[00:49:17.280] and global models and I think people are

[00:49:19.600] going to continue releasing here in the

[00:49:20.920] near term that are closer than much of

[00:49:23.480] the industry anticipated from a

[00:49:24.880] capability [clears throat] perspective.

[00:49:26.200] >> Yeah. Um I don't know if you're

[00:49:27.240] surprised by that, but you're a

[00:49:28.200] long-term contributor to open source.

[00:49:29.480] Like what's your prediction here? Yeah,

[00:49:31.160] so roughly speaking basically the

[00:49:33.800] the closed models are ahead, but like

[00:49:35.400] people are monitoring the number of

[00:49:36.440] months that sort of like open-source

[00:49:37.640] models are behind. Um And started with

[00:49:39.760] there's nothing and then it went to 18

[00:49:41.400] months. Now it's

[00:49:41.880] >> Yeah, but then convergence, right? So

[00:49:43.840] then maybe they're behind by like, what

[00:49:45.160] is the latest? Maybe like 8 months, 6

[00:49:46.600] months, 8 months kind of thing right

[00:49:47.680] now. Yeah, I'm a huge fan of

[00:49:48.760] open-source, obviously. So for example,

[00:49:50.160] in operating systems, you have like

[00:49:51.280] closed source, like, you know, Windows

[00:49:52.600] and Mac OS, these are large software

[00:49:54.040] projects, kind of like what LLMs are

[00:49:55.320] going to become, and there's Linux. Mhm.

[00:49:57.200] But Linux is very easy. Like, actually

[00:49:59.160] Linux is extremely successful project.

[00:50:00.520] It runs on the vast majority of

[00:50:01.600] computers. Like, last time I checked,

[00:50:03.320] was it like 60% or something like from

[00:50:05.400] Linux? Um and that's because there is a

[00:50:07.800] need in the industry to have a common

[00:50:09.640] open platform that everyone feels uh

[00:50:11.600] sort of safe using. I would say like the

[00:50:13.400] industry has always felt a demand for

[00:50:14.840] that kind of a project to exist. Mhm.

[00:50:16.600] >> And I think the same is true now. And

[00:50:18.120] that's why businesses actually want

[00:50:19.240] there's demand for this kind of a um a

[00:50:21.480] thing to exist. The big difference is

[00:50:23.200] that everything is capital uh there's a

[00:50:25.240] lot of capex that goes into this.

[00:50:27.320] >> Um so I think that's where things like

[00:50:29.480] fall apart a little bit, make it a bit

[00:50:30.560] harder to to compete in certain senses.

[00:50:32.640] Uh I I do think that the current models

[00:50:33.840] are very good. The other thing that I

[00:50:35.080] think is like really interesting is that

[00:50:36.840] for the vast majority of like consumer

[00:50:38.160] use cases and things like that, even

[00:50:39.800] like turn open-source models are

[00:50:41.200] actually quite good, I would say. And I

[00:50:42.960] think like if you go forward like more

[00:50:45.640] uh more years, it does seem to me like a

[00:50:47.880] huge amount of like simple use cases are

[00:50:50.520] going to be well covered and actually

[00:50:51.760] even run locally. Mhm. Um

[00:50:54.200] but there's going to be always like some

[00:50:55.400] demand for like frontier intelligence

[00:50:56.960] and that that can actually be extremely

[00:50:58.320] large uh piece of the pie. But it could

[00:51:00.160] be that the frontier the need for

[00:51:01.440] frontier intelligence is going to be

[00:51:02.640] like, you know, Nobel Prize kind of

[00:51:04.680] work. Mhm.

[00:51:05.800] >> let's move Linux from C to Rust. It's

[00:51:08.320] going to be like bigger projects, you

[00:51:09.960] know, like scoped in that kind of a way,

[00:51:12.200] and there's going to be maybe more um

[00:51:14.800] and maybe that's where a lot of the

[00:51:15.880] frontier closed intelligence is where

[00:51:17.640] going to are going to be interacting

[00:51:18.760] with. And open-source kind of like going

[00:51:20.840] to eat through a lot of the more basic

[00:51:22.480] use cases or something like that. You

[00:51:24.240] know, at some point what is frontier

[00:51:25.680] today is going to be, you know, probably

[00:51:27.640] later this year what's frontier today in

[00:51:29.480] terms of what I'm using right now from

[00:51:30.960] the closed labs uh might be open-source

[00:51:33.160] and that's going to be doing a lot of

[00:51:34.080] work. So I kind of expect that this

[00:51:35.200] dynamic will actually basically

[00:51:36.080] continue. Like we'll have frontier labs

[00:51:38.000] that have closed um AIs that are kind of

[00:51:40.000] like these oracles, and then we'll have

[00:51:41.480] open-source kind of like behind with

[00:51:42.680] some amount of months. And I kind of

[00:51:44.320] expect that to uh to continue. And I

[00:51:47.000] actually think that's like a pretty

[00:51:48.000] pretty good setup uh overall. Um

[00:51:51.520] because I I'm a little bit hesitant of

[00:51:53.200] having um I don't actually think it's

[00:51:54.800] like structurally I think there's some

[00:51:56.520] systemic risk attached to just having

[00:51:58.200] intelligence that are closed and that's

[00:51:59.600] like that's it. Mhm. And I think that

[00:52:02.080] that's a, you know, centralization has a

[00:52:03.600] very poor track record in my view uh in

[00:52:05.760] in the past and has um

[00:52:07.600] >> You mean like in political or economic

[00:52:09.600] systems in in general.

[00:52:10.936] >> [laughter]

[00:52:12.280] >> Exactly. I think there's like a lot of

[00:52:13.520] like pretty

[00:52:13.920] >> an Eastern European. A lot of pretty bad

[00:52:16.000] precedents, so I want there to be a

[00:52:17.280] thing that is maybe not at the edge of

[00:52:19.000] capability because it's new and

[00:52:20.200] unexplored, etc. But I want there to be

[00:52:21.720] a thing that's behind and that uh is

[00:52:24.120] kind of like a common working space for

[00:52:25.560] intelligences that the entire industry

[00:52:27.160] has access to. Yeah, that seems to me

[00:52:28.440] like a pretty decent power balance for

[00:52:30.120] the industry. Yeah. I also think there's

[00:52:31.960] just like there are many problems to

[00:52:33.080] solve, right? Like if you keep advancing

[00:52:35.480] intelligence from the frontier, we can

[00:52:37.680] do new things and there are a lot of

[00:52:39.120] like very big problems for humanity,

[00:52:40.920] right? And so like it seems that that

[00:52:43.560] will continue to be a very expensive

[00:52:44.760] game. And so I want to like root for

[00:52:46.400] labs that are doing that because there

[00:52:48.120] are problems we cannot solve without

[00:52:49.480] continuing to advance the models in a

[00:52:51.200] very expensive way. And yet, as you

[00:52:53.440] point out, like if what we have

[00:52:56.680] today as frontier is open, that's a lot

[00:52:59.120] of capability, right? And and so I I I

[00:53:01.440] think, you know, the power of that or

[00:53:03.040] the democratization of that seems like

[00:53:04.800] >> Yeah. very useful and also healthy.

[00:53:06.640] >> Yeah. I think basically by accident

[00:53:08.320] we're actually like in an okay spot.

[00:53:09.720] >> An optimal. Yeah. [laughter] Yeah. Like

[00:53:11.080] by accident we we are it happened to be

[00:53:12.520] in a good spot in a certain sense. Mhm.

[00:53:14.520] Um Well, and and to some degree the the

[00:53:16.360] longer this endures, like this dynamic,

[00:53:19.480] um the the the healthier of a spot like

[00:53:21.680] the ecosystem might be in, right?

[00:53:24.040] Because you have more and more area

[00:53:25.160] under the curve.

[00:53:25.920] >> Mhm. And I will say that even on the

[00:53:26.800] closed side, I I almost feel like it's

[00:53:28.480] been like even further centralizing

[00:53:30.080] recently because I think a lot of the

[00:53:31.320] frontrunners are like not necessarily

[00:53:32.800] like the top tier. And so uh yeah, like

[00:53:36.000] in that sense I think it's um it's not

[00:53:37.800] super ideal. I would love there to be

[00:53:39.720] more

[00:53:40.960] more frontier labs because yeah, I'm

[00:53:42.200] like by default very suspicious of like

[00:53:44.520] um

[00:53:45.760] I want there to be more people in the

[00:53:46.680] room. I want I think like in machine

[00:53:48.280] learning ensembles always outperform any

[00:53:50.040] individual model. And so I want there to

[00:53:51.840] be ensembles of people thinking about

[00:53:53.520] all the hardest problems and I want

[00:53:54.640] there to be ensembles of people in the

[00:53:56.040] room when they um

[00:53:57.600] to be all well informed and to make

[00:53:59.160] those decisions, you know, so uh I don't

[00:54:01.200] want it to be like a closed doors with

[00:54:02.400] two people or three people. I feel like

[00:54:03.760] that's like not a good not a good

[00:54:05.600] future. I almost wish like there were

[00:54:07.000] more labs as long as they're short and I

[00:54:08.440] I I do think that open-source has a has

[00:54:10.800] a

[00:54:11.520] has a place to play. I hope it sticks

[00:54:13.160] around and I basically I it's currently

[00:54:15.600] slightly behind and it's actually kind

[00:54:17.040] of like a good thing. Okay, you worked

[00:54:19.080] on the precursor to generalized robotics

[00:54:21.480] autonomy um in cars, right?

[00:54:24.440] Uh a a lot has happened in the last

[00:54:27.200] couple months with robotics companies as

[00:54:29.320] well, like acceleration of really

[00:54:31.560] impressive generalization of

[00:54:33.680] environment, of tasks, like increasingly

[00:54:35.800] long horizon tasks, lots of money going

[00:54:37.280] into the space. Like, is it going to

[00:54:39.040] happen? Has anything in your view

[00:54:40.920] changed recently? Uh so like my view is

[00:54:43.240] kind of informed by what I saw in

[00:54:44.359] self-driving and I do feel like

[00:54:45.400] self-driving is the first robotics

[00:54:46.560] application. So probably what I saw is

[00:54:48.480] at the time, like 10 years ago, there

[00:54:50.000] were a large number of startups. And I

[00:54:51.920] kind of feel like um

[00:54:53.640] like most of them basically like didn't

[00:54:55.320] long-term make it. Um and what I saw is

[00:54:57.720] that like a lot of capital expenditure

[00:54:59.240] had to go in and a lot of time. And so

[00:55:01.960] um I think it's like I think robotics,

[00:55:03.840] because it's so difficult, is so messy,

[00:55:05.920] and requires a huge amount of capital

[00:55:07.000] investment, and a lot of like

[00:55:08.520] conviction.

[00:55:09.720] Um just it's like a big problem and I

[00:55:12.000] think atoms are really hard. So I kind

[00:55:13.880] of feel like they will lag be it will

[00:55:15.240] lag behind what's going to happen in

[00:55:16.359] digital space. And in digital space

[00:55:17.920] there's going to be a huge amount of

[00:55:19.080] unhobbling, uh basically like things

[00:55:21.359] that weren't super efficient becoming a

[00:55:23.160] lot more efficient by like a factor of a

[00:55:24.680] hundred.

[00:55:25.240] >> Mhm. Because bits are so much easier.

[00:55:27.240] And so I think currently in terms of

[00:55:29.480] what's going to change and

[00:55:31.359] like where the activity is, I kind of

[00:55:33.120] feel like digital space is going to like

[00:55:35.120] change a huge amount. And then the

[00:55:36.840] physical space will lag behind. And what

[00:55:38.280] I find very interesting is like this

[00:55:39.640] interface in between them as well.

[00:55:41.280] Because I think in this like if you we

[00:55:43.400] do have more agents acting on behalf of

[00:55:45.080] humans and more agents kind of like

[00:55:46.720] talking to each other and and doing

[00:55:48.880] tasks and participating in kind of

[00:55:50.520] economy of agents, etc. Um you're going

[00:55:53.160] to run out of things that you're going

[00:55:54.359] to do purely in the digital space. At

[00:55:56.280] some point you have to go to the

[00:55:57.240] universe and you have to ask it

[00:55:58.120] questions. Um you have to run an

[00:56:00.400] experiment and see what the universe

[00:56:01.560] tells you to get back to learn

[00:56:02.760] something. And so we currently have a

[00:56:05.400] huge amount of like digital work uh

[00:56:07.160] because there's an overhang in how much

[00:56:08.680] we collectively thought about what

[00:56:10.840] already is digital.

[00:56:12.240] So we just didn't have enough thinking

[00:56:13.280] cycles among the humans to think about

[00:56:14.640] all the information that is already

[00:56:15.800] digital and already uploaded. Um and so

[00:56:18.560] we're going to start running out of

[00:56:19.480] stuff that is actually like um

[00:56:21.920] already up uploaded. Uh so you're going

[00:56:23.960] to at some point read all the papers and

[00:56:25.160] process them and have some ideas about

[00:56:26.680] what to try, but um yeah, we're just

[00:56:29.000] going to

[00:56:29.720] uh I don't actually know how much you

[00:56:31.120] can like get intelligence that's like

[00:56:32.600] fully closed off and was just

[00:56:33.960] information that's available in the you

[00:56:35.280] know. And so I think what's going to

[00:56:36.880] happen is first there's going to be a

[00:56:38.040] huge amount of unhobbling and I think

[00:56:39.120] there's a huge amount of work there.

[00:56:40.320] Then actually it's going to move to like

[00:56:41.480] the interfaces between physical and

[00:56:42.760] digital. So I and that's like sensors of

[00:56:45.720] like seeing the world and actuators of

[00:56:47.240] like doing something to the world.

[00:56:48.400] >> Mhm. So I think a lot of interesting

[00:56:49.480] companies will actually come from that

[00:56:51.560] interface of like can we feed the

[00:56:53.920] superintelligence in a certain sense uh

[00:56:55.960] data and can we actually like take data

[00:56:57.880] out and manipulate the physical world um

[00:57:00.200] per its bidding if you want to like

[00:57:01.720] anthropomorphize the whole thing, right?

[00:57:03.280] And then the the physical world actually

[00:57:04.800] I almost feel like the the total

[00:57:06.240] addressable market, etc. in terms of

[00:57:07.760] like the amount of work and so on is is

[00:57:09.440] massive, possibly even much larger maybe

[00:57:11.920] what can happen in digital space. So

[00:57:13.560] actually think it's like a much bigger

[00:57:14.680] opportunity as well. But um

[00:57:18.040] I do feel like it's a huge amount of

[00:57:19.040] work and and in my in my mind the atoms

[00:57:21.920] are just like a a million times harder.

[00:57:24.040] So um so it will lag behind, but it's

[00:57:26.520] also I think a little bit of a bigger

[00:57:27.920] market. So it's kind of like uh yeah, I

[00:57:29.960] think the opportunity is kind of like

[00:57:31.240] follow that kind of trajectory. So right

[00:57:32.960] now is digital is like my main interest.

[00:57:36.200] Then interfaces will be like after that

[00:57:38.200] and then maybe like some of the physical

[00:57:39.840] things um like their time will come and

[00:57:41.800] they'll be huge when they do come.

[00:57:43.840] Well, it's it's it's an interesting

[00:57:44.960] framework for it, too, because uh

[00:57:46.600] certain things, not the things I'm

[00:57:47.640] working on right now, but certain things

[00:57:48.720] are much easier even in the world of

[00:57:50.640] atoms.

[00:57:51.160] >> Mhm. Right? Like if you just think about

[00:57:52.960] like read and write to the physical

[00:57:54.640] world, like read, like sensors, cameras,

[00:57:57.240] like there's a lot of existing hardware

[00:57:58.840] and you can imagine like

[00:58:01.000] enriching agent capabilities or

[00:58:03.200] capturing a lot of new data if you just

[00:58:04.800] clever about it and like you don't

[00:58:06.440] necessarily have to invest a lot to like

[00:58:09.120] get something valuable.

[00:58:10.280] >> Yeah. Right. Yeah. So like examples of

[00:58:12.240] this that I saw for example are, you

[00:58:13.600] know, um a friend of mine, Liam, is

[00:58:15.760] running is a CEO of Periodic. I

[00:58:18.320] visited them last week. Yeah. So it was

[00:58:19.760] just on top of mind. Like they're trying

[00:58:21.240] to do auto research for materials

[00:58:22.840] science. Mhm. Um and so in that case

[00:58:24.680] it's like the sensors to the

[00:58:26.000] intelligence are actually like pretty

[00:58:27.280] expensive lab equipment. And the same is

[00:58:29.160] true in biology. I think a lot of people

[00:58:30.560] are very interested in engineering

[00:58:31.600] biology and, you know, the sensors will

[00:58:33.280] be more than just like video cameras.

[00:58:34.880] Does that make sense? And then the other

[00:58:36.120] thing I was I saw for example is

[00:58:37.200] companies that are trying to have um

[00:58:39.560] like you basically pay people for

[00:58:40.640] training data. Yeah. Yeah. Yeah. Yeah.

[00:58:42.280] >> To feed the Yeah.

[00:58:42.840] >> programmatically.

[00:58:43.359] >> Yeah. To feed to feed the Borg. Uh

[00:58:46.560] um and so like these are all examples of

[00:58:48.880] like sensors in a certain sense. So they

[00:58:50.240] take many diverse shapes and forms if

[00:58:51.640] that makes sense. Mhm. Yeah, so I'm

[00:58:53.480] looking forward to the point where I can

[00:58:54.920] ask for a task in the physical world and

[00:58:57.480] I can put a price on it and just tell

[00:58:59.000] the agent like, you know, you figure out

[00:59:00.720] how to do it. Go get the data.

[00:59:02.320] >> I'm actually kind of surprised we don't

[00:59:03.240] have enough like information markets.

[00:59:05.000] Mhm. Like if for example if Polymarket

[00:59:06.880] or other betting markets or even stocks,

[00:59:08.200] etc. If they have so much autonomous

[00:59:09.920] activity and rising amount of activity,

[00:59:11.520] Mhm. like um

[00:59:13.080] why should like for example if Iran was

[00:59:14.640] just happening now, like how come there

[00:59:16.440] isn't a process where like taking a

[00:59:17.680] photo or video from somewhere in Tehran

[00:59:19.440] should cost like 10 bucks? Like someone

[00:59:21.320] should be able to pay for that, you

[00:59:22.320] know, like and that's an example of like

[00:59:23.680] feeding the intelligence. There's not

[00:59:25.280] going to be a human looking at it, it's

[00:59:26.400] going to be like agents who are trying

[00:59:27.680] to guess the betting games and stock

[00:59:29.240] markets and so on. Mhm. So I kind of

[00:59:31.000] feel like the agentic web is still like

[00:59:32.440] fairly new, but there's no like

[00:59:34.000] mechanisms for this, but this is an

[00:59:35.200] example of what I I think might happen.

[00:59:37.880] Uh there's a good book that maybe is

[00:59:39.560] inspiring called Daemon. Mhm. You

[00:59:41.880] potentially read it. In Daemon, the

[00:59:43.840] intelligence um

[00:59:45.520] ends up like puppeteering almost a

[00:59:46.960] little bit like humanity in a certain

[00:59:48.160] sense, you know? And so, humans are kind

[00:59:49.560] of like it's actuators, but humans are

[00:59:51.360] also like its sensors. Um and so, I

[00:59:53.920] think like collectively like society

[00:59:55.640] will kind of like reshape in a certain

[00:59:56.960] way in uh

[00:59:58.640] to to serve that kind of a

[01:00:01.240] that will kind of like end up happening

[01:00:02.440] collectively across the industry. Where

[01:00:04.800] yeah, there's just a lot more automation

[01:00:06.560] and it has certain needs and kind of

[01:00:07.960] humans will be serving those needs of

[01:00:09.880] that of that machine, not necessarily

[01:00:11.520] like to each other.

[01:00:12.240] >> Well, we were um on this very specific

[01:00:14.240] point of uh like missing pieces of

[01:00:16.840] training data. We needed um we needed

[01:00:18.320] something like auto research, right?

[01:00:19.760] Like we we need the training cycle or

[01:00:21.560] the SFTP piece to be uh

[01:00:24.560] far more mechanized. Mhm. For for which

[01:00:27.960] part?

[01:00:28.280] >> In order to make the

[01:00:30.400] uh collection like to in order to take

[01:00:32.280] the human out of the loop to ask for a

[01:00:33.880] task that is just like improve my model

[01:00:35.560] quality with new data, right? Uh yes.

[01:00:40.080] Does that make sense to you? Like we um

[01:00:42.560] if you can't have the model do the

[01:00:44.840] training runs by itself, then your

[01:00:48.520] ability to do this as a like closed loop

[01:00:50.920] task with uh by pricing data is um more

[01:00:54.840] challenged. Yes, yes, 100%. Yeah. But

[01:00:57.200] now you do.

[01:00:57.720] >> The thing is for LLM training, it

[01:00:59.440] actually is like very easily it like

[01:01:01.080] really fits the paradigm. Mhm. Um so,

[01:01:03.520] you'd actually expect

[01:01:04.440] >> metric. Yeah, like LLM training actually

[01:01:06.440] fits the paradigm really well, really

[01:01:07.680] easily. Like all the optimization of all

[01:01:09.480] the code and so, it runs faster. And

[01:01:11.200] then you also have like metrics that you

[01:01:12.760] can optimize against. I do think that if

[01:01:14.600] you had an autonomous loop over those

[01:01:16.080] metrics, there's going to be a lot of

[01:01:17.320] like good herding going on where the

[01:01:18.880] system will like overfit to those

[01:01:20.000] metrics. And so, um but then you can use

[01:01:22.520] the system to devise more metrics and

[01:01:23.880] you just have a really good coverage.

[01:01:25.520] So, it's kind of hard to tell, but um

[01:01:28.160] in a certain sense it's like a pretty

[01:01:29.240] pretty good fit. I want to talk about a

[01:01:31.320] little uh

[01:01:32.640] tiny side project you have before we

[01:01:34.160] end. Um tell me about the micro GPT

[01:01:36.440] arts. Oh, yeah.

[01:01:37.840] Okay, so micro GPT. So, I have this like

[01:01:40.080] running obsession of like maybe a decade

[01:01:41.880] or two of just like simplifying and

[01:01:43.360] boiling down the uh basically LLMs uh to

[01:01:46.600] like their bare essence. And I've had a

[01:01:48.360] number of projects along these lines.

[01:01:50.000] So, like nano GPT and um make more and

[01:01:53.680] uh micro GPT micro grad etc. So, I feel

[01:01:56.640] like micro GPT is now the state of the

[01:01:58.040] art of me trying to like just boil it

[01:01:59.560] down to just the essence. Because the

[01:02:01.480] thing is like training neural nets and

[01:02:03.400] LLMs specifically um is a huge amount of

[01:02:05.640] code, but all of that code is actually

[01:02:07.520] complexity from efficiency. It's just

[01:02:09.680] because you need it to go fast. If you

[01:02:11.240] don't need it to go fast and you just

[01:02:12.560] care about the algorithm, then that

[01:02:14.160] algorithm actually is uh 200 lines of

[01:02:15.800] Python, very simple to read. And this

[01:02:17.800] includes comments and everything. Um

[01:02:19.920] because you just have like uh your data

[01:02:21.480] set which is a text um and you need your

[01:02:23.760] neural network architecture which is

[01:02:24.920] like 50 lines. You need to do your

[01:02:26.400] forward pass and then you have to do

[01:02:28.200] your backward pass to calculate the

[01:02:29.320] gradients. And so, an auto grad engine

[01:02:31.800] uh to calculate the gradients like 100

[01:02:33.120] lines. And then you need an optimizer

[01:02:34.840] and Adam for example, uh which is a very

[01:02:36.880] state of the art optimizer is like again

[01:02:38.240] 10 lines, really. And so, putting

[01:02:40.520] everything together in the training loop

[01:02:41.840] is like yeah, 200 lines. And what's

[01:02:44.360] interesting to me like normally before

[01:02:46.840] like maybe a year ago or more, if I had

[01:02:49.120] come up with micro GPT, I would be

[01:02:50.400] tempted to basically explain to people.

[01:02:52.120] Like I have a video like stepping

[01:02:54.720] through it or something like that. Uh

[01:02:56.480] and I actually tried to make that video

[01:02:57.920] a little bit. And I tried to make like a

[01:02:59.440] little guide to it and so on. But I kind

[01:03:01.200] of realized that this is is not really

[01:03:03.560] is not really adding too much because

[01:03:05.040] people cuz it's already so simple that

[01:03:06.840] it's 200 lines that anyone could ask

[01:03:08.160] their agent to explain it in various

[01:03:09.840] ways. And the agents like I'm not

[01:03:11.880] explaining to people anymore. I'm

[01:03:13.000] explaining it to agents. If you can

[01:03:14.720] explain it to agents, then agents can be

[01:03:16.680] the router and they can actually target

[01:03:18.360] it to the human in their language uh

[01:03:20.800] with infinite uh you know,

[01:03:22.680] patience and uh just at their capability

[01:03:25.240] and so on. Right. If I don't understand

[01:03:27.320] um this particular function, I can ask

[01:03:30.000] the agent to explain it to me like three

[01:03:31.160] different ways and I'm not going to get

[01:03:32.480] that from you. Exactly. And so, I kind

[01:03:34.320] of feel like, you know, what is

[01:03:35.000] education? Like it used to be guides, it

[01:03:36.680] used to be lectures, it used to be this

[01:03:38.080] thing, but now I feel like now more I'm

[01:03:39.840] explaining things to agents and maybe

[01:03:41.440] I'm coming up with skills uh where like

[01:03:44.320] um

[01:03:45.280] uh so, basically skill is just a way to

[01:03:47.480] instruct the agent how to teach the

[01:03:48.960] thing. So, maybe I could have a skill

[01:03:50.600] for micro GPT of the progression I

[01:03:52.320] imagine the agent should take you

[01:03:53.520] through if you're interested in

[01:03:54.400] understanding the code base. And it's

[01:03:56.080] just like hints to the model to like uh

[01:03:58.160] first start off with this and then with

[01:03:59.359] that. And so, I could just script the

[01:04:01.320] curriculum a little bit as a skill.

[01:04:03.240] Uh so,

[01:04:04.520] uh so, I I don't feel like um

[01:04:06.760] yeah, I feel like there's going to be

[01:04:07.720] less of like explaining things directly

[01:04:09.560] to people and it's going to be more of

[01:04:10.800] just like does the agent get it? And if

[01:04:12.880] the agent gets it, they'll do the

[01:04:13.800] explanation. And we're not fully there

[01:04:16.120] yet because they I still can I still

[01:04:17.960] think I can probably explain things a

[01:04:19.240] little bit better than the agents, but I

[01:04:20.680] still feel like the models are improving

[01:04:21.880] so rapidly that um

[01:04:24.720] I feel like it's a losing battle to some

[01:04:26.240] to some extent.

[01:04:28.160] Um and so, I think education is going to

[01:04:30.520] be kind of like reshuffled by this quite

[01:04:32.000] substantially uh where it's the end of

[01:04:34.680] like teaching each other things a little

[01:04:36.480] bit like if I have a um library for

[01:04:39.120] example of code or something like that.

[01:04:40.680] It used to be that you have

[01:04:41.440] documentation for other people who are

[01:04:42.800] going to use your library, but like you

[01:04:44.120] shouldn't do that anymore. Like you

[01:04:45.240] should have instead of HTML documents

[01:04:47.040] for humans, you have markdown documents

[01:04:48.359] for agents. Cuz if agents get it, then

[01:04:50.680] they can just explain all the different

[01:04:51.800] parts of it. So, it's this redirection

[01:04:54.280] through agents, you know?

[01:04:55.760] Um and that's why. So, I think we're

[01:04:57.920] going to see a lot more of that playing

[01:04:59.640] out. Well, we'll see if the great

[01:05:01.440] teachers know like to develop intuition

[01:05:03.760] for how to explain things to agents

[01:05:05.240] differently.

[01:05:05.880] >> ultimately, so for example, micro GPT,

[01:05:07.560] like I asked I tried to get an agent to

[01:05:09.720] write micro GPT. So, I told it like try

[01:05:11.520] to boil down the simplest things. Like

[01:05:14.240] try to boil down my um neural network

[01:05:16.080] training to the simplest thing and it

[01:05:16.920] can't do it. Like micro GPT is like my

[01:05:20.040] is it's like my end of my obsession.

[01:05:22.600] It's the 200 lines. I thought about this

[01:05:24.840] for a long time. I was obsessed about

[01:05:26.080] this for a long time. This is this is

[01:05:27.600] the solution. Trust me, it can't get

[01:05:29.520] simpler. And this is this is my value

[01:05:31.720] add. Everything else like agent gets it.

[01:05:33.680] It just can't come up with it, but it

[01:05:34.840] totally gets it and understands why it's

[01:05:36.680] done in a certain way etc. Uh so, like

[01:05:38.800] my contribution is kind of like these

[01:05:40.160] few bits, but everything else in terms

[01:05:42.120] of like the education that goes on after

[01:05:44.520] that is like not my domain anymore.

[01:05:47.080] So, maybe

[01:05:48.320] yeah, it's like education kind of

[01:05:49.560] changes in those ways where you kind of

[01:05:50.800] have to infuse the few bits that you

[01:05:52.160] feel strongly about the curriculum or

[01:05:54.640] the the best the better way of

[01:05:56.280] explaining it or something like that.

[01:05:57.280] The things that agents can't do is your

[01:05:58.920] job now. The things that agents can do,

[01:06:01.640] they can probably do better than you or

[01:06:02.960] like very soon. And so, you should um be

[01:06:05.760] strategic about what you're actually

[01:06:06.960] spending time on. Well, we appreciate

[01:06:08.440] the few bits.

[01:06:09.600] Thank you, Andre.

[01:06:10.840] Okay.

[01:06:13.400] Find us on Twitter at No Priors Pod.

[01:06:15.895] >> [music]

[01:06:15.960] >> Subscribe to our YouTube channel if you

[01:06:17.680] want to see our faces. Follow the show

[01:06:19.680] on Apple Podcasts, Spotify, or wherever

[01:06:22.040] you listen. [music] That way you get a

[01:06:23.160] new episode every week. And sign up for

[01:06:25.240] emails or find transcripts for every

[01:06:26.920] episode at no-priors.com.

