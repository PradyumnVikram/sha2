# Reduced Round SHA2 Collisions 
This repository refactors and documents the code provided by the authors of the research paper, "New Records in Collision Attacks on SHA-2". The repository contains two folders

1. `collision_verify`: This is a refactored version of the previous `verify_result` folder in the original repository. The tooling for `verify_result` is simply a routing mechanism for configuring instances of SHA2 encryption algorithm, varying the number of rounds, or type of collision (`FS`, `SFS`, or complete). No major work regarding documentation is required on this part of the tooling.

2. `find_dc`: This part of the repository contains all the code which does the actual work of finding the differential characteristics, improving them, and finding the actual messages which are colliding. 

### Missing Elements

1. No code for actually finding the colliding messages, though that's not the goal either. 
2. No proper explanations for the choice of optional parameters. 
