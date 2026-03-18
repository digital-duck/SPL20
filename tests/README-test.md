● All 5 adapters are already implemented and registered:                                                                
                                                            
  ┌────────────┬──────────┬─────────────────────────────────────────────────────────┐                                   
  │  Adapter   │  Status  │                       How to use                        │                                   
  ├────────────┼──────────┼─────────────────────────────────────────────────────────┤                                   
  │ echo       │ Built-in │ spl2 run file.spl (default, no setup)                   │                                   
  ├────────────┼──────────┼─────────────────────────────────────────────────────────┤
  │ claude_cli │ Built-in │ spl2 run file.spl --adapter claude_cli                  │
  ├────────────┼──────────┼─────────────────────────────────────────────────────────┤                                   
  │ openrouter │ Built-in │ export OPENROUTER_API_KEY=... then --adapter openrouter │                                   
  ├────────────┼──────────┼─────────────────────────────────────────────────────────┤                                   
  │ ollama     │ Built-in │ --adapter ollama (needs Ollama running)                 │                                   
  ├────────────┼──────────┼─────────────────────────────────────────────────────────┤
  │ momagrid   │ Built-in │ export MOMAGRID_HUB_URL=... then --adapter momagrid     │                                   
  └────────────┴──────────┴─────────────────────────────────────────────────────────┘
                                                                                                                        
  To test with Ollama right now:                            
                                                                                                                        
  # Make sure Ollama is running with a model
  ollama pull llama3.2                                                                                                  
  ollama serve   # if not already running                                                                               
                                         
  # Then run any SPL file                                                                                               
  spl2 run examples/hello_world.spl --adapter ollama                                                                    
  spl2 run examples/hello_world.spl --adapter ollama -p user_input="What is SPL?"
                                                                                                                        
  You can also specify a model in the .spl file with USING MODEL 'llama3.2'. Want to try it out?      