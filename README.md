# Eigen Trust Network (ETN) Discord Bot

Trust is powerful. Knowing who is capable, value aligned, or has done good work in the past is extremely valuable for all sorts of decisions, but currently it takes lots of effort to collect this information. Imagine if you could leverage your trust network's collective knowledge to get a read of hundreds or thousands of times as many people, with minimal effort!

That is what EigenTrust Network is creating. We use an algorithm similar to Google's PageRank to model trust propagation, setting the subjective source of all trust to each individual. So that from your personal view of the network you can see how much of your trust has flowed to anyone else.

This specific repository is for the ETN Discord Bot.

## How to Use

Setting up ETN on your Discord server is easy. First, click on [this link](https://discord.com/api/oauth2/authorize?client_id=999817950880075949&permissions=274878237760&scope=bot) and select the server you wish to add the ETN to.  Next, in that server, you will want to specify what reactions equal what flavor of trust.  For example, `!etn add_trust_react :thumbsup: "general"` will bind the :thumbsup: react to a vote in the general trust flavor.  Custom reacts are allowed.  And you're done!  You can now vote with any reacts you've configured, or you can use the :mag: (`:mag:`) react to see how much you and your network trusts a user in every category the server has a react for.

To remove a react you can say `!etn remove_trust_react :thumbsup:`. To see what reacts a server has say `!etn list_trust_reacts`.  To see a list of available commands simply say `!etn help`.
