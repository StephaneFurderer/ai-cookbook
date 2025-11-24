# I. Actuaries should own their pipelines
Let’s build something practical today. 
A rapid-prototyping automation for insurance operations, powered by Python, n8n and FastAPI. 

Our use case is a travel-insurance company. 
Your core risk exposure is the number of travelers flying into specific airports across your portfolio. 
When a hurricane begins to form in the Atlantic, you need to know, fast, how many travelers are heading into the impact zone.

By the end of this session, you’ll have a pipeline that 
- watches emerging events,
- reads the signals,
- predicts the exposure,
- and alerts your operations automatically.

No scrambling. No manual stitching. 
A service that pulls event data every day, blends it with your traveler volumes, estimates who’s at risk, and sends a clear action straight to your ops inbox through Gmail.

One small system, reliable, and tailored to your risks. 
And after today, you’ll know how to build it yourself so that your team can move quicly when it matters.

# II. How To Think Automation in 2025? 3 Pain Points And 1 Framework

## 3 Painpoints shared by most of actuarial departments - studies show:

3 Painpoints that get in the way of leveraging more value out of actuarial departments:

(1) How to ingest new data? In Real time? (modularity)
(2) How to turn our models / business logic into a pipeline? (production-ready)
(3) How fast is it for our ideas to be integrated into existing architecture (ecosystem)

## Actuarial strength: quickly blend in-house systems with external-high-quality data
So in this section, I want to walk you through how we think about integrating external forecast data into an operational predictive pipeline, and why this matters more than ever.

Today, our predictive model is strong — it’s our in-house intelligence layer.
But increasingly, the value doesn’t come only from what we build internally. 
It comes from how quickly we can blend our internal predictions with high-quality, real-time data from outside.

And in 2025, this external data landscape has completely changed.

## POV: AI-based weather models from Google outperforming traditional methods.
For the first time, AI-based weather models like the ones Google has released to the community are outperforming traditional meteorological methods. 
These models are incredibly accurate, and they’re freely accessible. 
This means that the companies who are able to rapidly source, integrate, and operationalize these forecasts will get a material edge in risk anticipation.

So the challenge becomes:
> How do we take these raw, external data feeds… and make them usable, consistent, and scalable inside our predictive pipeline?

Let’s take hurricanes as an example.

You can download historic and real-time storm forecasts as CSVs. But manually pulling, cleaning, structuring, and feeding them into your model is slow, error-prone, and absolutely not scalable when you need real-time decisions.
This is where modularity becomes essential.

## 1 Framework: Think Modules

We build a small in-house API on top of these external datasets — a clean interface that retrieves the data, formats it properly, and exposes it so your automation tools and models can digest it reliably.
The moment you do that, something powerful happens:
You turn a one-off technical task into a reusable module.

Now anytime you need hurricane forecasts — for any use case, any team, any pipeline — you simply call your internal API. No more reinventing the wheel. No manual massaging. No fragile ad-hoc scripts.

From there, your automation layer can orchestrate the entire flow:
	•	A trigger runs daily during hurricane season
	•	The API pulls and formats the new forecast
	•	Your predictive model calculates exposure — number of travelers, airports affected, etc.
	•	Then you apply a simple triage logic: low, medium, high risk
	•	And finally, you send an actionable message to operations

The beauty of this structure is not just the workflow.
It’s the architecture.
Everything is decomposed into modules you can reuse, extend, and plug into other pipelines.

To build all that quickly, we use tools like n8n for orchestration, Railway for lightweight API hosting, and FastAPI for packaging both data access and model predictions. 
This becomes your innovation stack — fast, flexible, and perfect for prototyping or demonstrating value internally.

So the purpose of this section is simple:
Show that modern predictive operations are not just about better models — they are about better pipelines.
Pipelines that source the right data, format it correctly, combine it intelligently, and surface only what the business needs to act.

# III. How To Build Lightweight API using FASTAPI and RAILWAY

Alright, so now let’s jump into the third section of our presentation, where I’m going to show you how we can very quickly create and deploy an API that powers the automation layer we discussed earlier.

The goal here is not to turn anyone into a software engineer.
The goal is :
(1) to show you how simple and approachable these tools have become, AND
(2) how actuaries can work hands-on with modern data products without needing a full IT project.

So let’s get started.

## Structure your API into small components
In one of his videos, Dave Ebbelaar explains a clean way to structure API applications using three layers:
the domain, the router, and the endpoints.
If you want to go deeper into building large-scale APIs, I really encourage you to watch that.
https://www.youtube.com/watch?v=-IaCV5-mlSk


But for today, we’ll take a lighter, more practical version.

I’ll start by opening a simple Python file.
This will be our entry point — the place where the FastAPI application is created.
All we do here is call FastAPI() and then include a router.

The router is just another Python file.
Its job is to define what our API does — in this case, fetch external hurricane forecast data.
Inside the router, we call a small helper module, a data fetcher, whose only job is to download the CSV from Google DeepMind’s WeatherLab for a given date.

Once we download the CSV, we do a bit of light data manipulation.
Nothing complex — just reshaping the columns so they match the format our predictive models expect.
This step is important because your models rely on consistent inputs, and this is where we enforce that consistency.

So at this point, we have three things:
	1.	A FastAPI app
	2.	A router defining an endpoint
	3.	A data-fetching module that retrieves and formats the data

That’s our API.

## Package it so that it can be accessible from anywhere using RAILWAY
Next, we package it so it can run anywhere.
To do that, we add two simple files:
	•	A Dockerfile, which tells Railway how to build the container
	•	A railway.toml, which tells Railway how to run the app once it’s deployed

That’s it — our API is ready.

So now I switch to Railway.
Here I’ll create a new application, connect it to the code, and deploy it.
Railway builds the container for us, sets up the URL, and our API goes live in less than a minute.

## Tiny Streamlit Interface
Once the API is deployed, I want to show you how you can actually use it — so we’ll build a tiny Streamlit interface.
Streamlit is great because it allows us to interact with the API visually without writing any frontend code.

In Streamlit, I simply call our new API endpoint, fetch the data, and display it on the screen.
And what we see is important:
We are no longer relying on manual downloads, spreadsheets, or ad-hoc scripts.
We’re consuming the data through our own in-house API.

## Conclusion
This means it’s repeatable.
It’s consistent.
It’s scalable.
And it can be plugged directly into any predictive model or automation pipeline we want.

So the purpose of this step is to show you that building production-like components is not only accessible — it’s fast.
And once you have these API modules, they become building blocks you can reuse across many operational workflows.


