# Design

- it should be very easy to support common applications (sane defaults)
- it should be easy to tweak certain settings
- it should be easy to extend or support differing configurations

# Rough flow
1. kreate Kontext object
   - add modules
2. kreate Cli Object
   - call init_cli on all modules
     - add options
     - add commands
   - Cli.run
3. kreate Konfig object
   - inklude all kinds of konf files
4. kreate App object
   - kreate all komponents from konfig
5. run subcmd
   - most subcommands run kreate_files
   - view mostly views the konfig
