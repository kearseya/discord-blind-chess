from .chesscog import chesscog

def setup(bot):
    bot.add_cog(chesscog(bot))