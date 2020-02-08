# ladder
This application can be used to manage the rankings of players participating in a club ladder competition.

It is built using the Python Django framework.  It was used as a vehicle to learn both Python and Django.  Hopefully the
code gets better as I learn more.  

A <code>Ladder</code> consists out of one or more <code>LadderRound</code>s. 

<code>Players</code> can enter or leave a <code>LadderRound</code> while the <code>LadderRound</code> is not in a closed status.

##LadderRound
a <code>LadderRound</code> consists out of a <code>list</code> of <code>Players</code>.  This <code>list</code>.  Each <code>Player</code> 
has a <code>Player.ranking</code> which is linked to <code>round.PlayerRanking</code>

