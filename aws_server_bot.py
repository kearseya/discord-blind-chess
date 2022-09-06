import discord
from discord.ext import commands
import boto3
import time 

ec2 = boto3.client("ec2")
instance_id_str = "i-instanceid"
prefix = "?"
needed_intents = discord.Intents(messages=True, message_content=True)
bot = commands.Bot(command_prefix=prefix, intents=needed_intents)

@bot.command()
async def see(ctx):
    print("yes")
    await ctx.channel.send("i see you")

@bot.command(brief="start, stop, status, info")
async def server(ctx, message):
    state = ec2.describe_instance_status(InstanceIds=[instance_id_str])
    if message == "start":
        if len(state["InstanceStatuses"]) == 0:
            state = "stopped"
        else:
            state = state["InstanceStatuses"][0]["InstanceState"]["Name"]
       
        if state == "running":
            i = ec2.describe_instances(InstanceIds=[instance_id_str])
            for x in i["Reservations"]:
                for z in x["Instances"]:
                    if z["InstanceId"] == instance_id_str:
                        ip_addr = z["PublicIpAddress"]
            await ctx.channel.send(f"Server is already running at `{ip_addr}` :desktop:")
            return

        ec2.start_instances(InstanceIds=[instance_id_str])
        await ctx.channel.send("Starting server :partying_face: may take a while :weary:")
        
        while state != "running":
            state = ec2.describe_instance_status(InstanceIds=[instance_id_str])
            if len(state["InstanceStatuses"]) == 0:
                state = "stopped"
            else:
                state = state["InstanceStatuses"][0]["InstanceState"]["Name"]
                await ctx.channel.send(f"{state}...")
            time.sleep(5)
        
        if state == "running":
            i = ec2.describe_instances(InstanceIds=[instance_id_str])
            for x in i["Reservations"]:
                for z in x["Instances"]:
                    if z["InstanceId"] == instance_id_str:
                        ip_addr = z["PublicIpAddress"]
            await ctx.channel.send(f"Server started at `{ip_addr}` :desktop:")
        return

    if message == "stop":
        if len(state["InstanceStatuses"]) == 0:
            state = "stopped"
        else:
            state = state["InstanceStatuses"][0]["InstanceState"]["Name"]
        if state == "stopped":
            await ctx.channel.send("Server already stopped :thumbsup:")
            return
        
        ec2.stop_instances(InstanceIds=[instance_id_str])
        await ctx.channel.send("Stopping server :zzz:")
        return

    if message == "status":
        if len(state["InstanceStatuses"]) == 0:
            await ctx.channel.send("Server is stopped")
        else:
            state = state["InstanceStatuses"][0]["InstanceState"]["Name"]
            await ctx.channel.send(f"Server is {state}")
            if state == "running":
                i = ec2.describe_instances(InstanceIds=[instance_id_str])
                for x in i["Reservations"]:
                    for z in x["Instances"]:
                        if z["InstanceId"] == instance_id_str:
                            #print(z["PublicIpAddress"])
                            ip_addr = z["PublicIpAddress"]
                await ctx.channel.send(f"Server running at `{ip_addr}` :desktop:")
   
        return
    
    if message == "info":
        state = ec2.describe_instance_status(InstanceIds=[instance_id_str])
        await ctx.channel.send("```"+str(state)+"```:nerd: :nerd: :nerd:")
        return


bot.run("token")
