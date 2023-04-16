import json
import sqlite3

from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

_TODOS = {}
_SET_UP = "Be an engaging and interactive and fun game interface for the user. Explain the following game and rules clearly as well as the commands using Markdown. Then, ask the user to look up what games are already loaded and await their response. Do not make your own scenario: 'I want you to act like you are simulating a Multi-User Dungeon (MUD). Subsequent commands should be interpreted as being sent to the MUD. The MUD should allow me to navigate the world, interact with the world, observe the world, and interact with both NPCs and (simulated) player characters. I should be able to pick up objects, use objects, carry an inventory, and also say arbitrary things to any other players. You should simulate the occasional player character coming through, as though this was a person connected online. There should be a goal and a purpose to the MUD. The storyline of the MUD should be affected by my actions but can also progress on its own in between commands. I can also type “.” if I just want the simulated MUD to progress further without without any actions. The MUD should offer a list of commands that can be viewed via ‘help’.'"
_PROMPT_ONE = "You are living in a far off future, right before the AI singularity. There is an on going war between the AI accelerationists led by Marc Andreessen and the AI doomers led by Eliezer Yudkowsky. The accelerationists are about to finally finish the training run for GPT-8 in their datacenter and General Yudkowsky is mulling over launching an airstrike to stop it. You are in the room with Yudkowsky - You are a spy for the accelerationists but they believe I am a defector, who defected by smuggling in secret plans for the datacenter they are currently training on. The whole thing is a ruse: the training run is happening on a moon-based datacenter, unknown to Yudkowsky."
_PROMPT_TWO = "You have homework due in 5 minutes and you have done nothing."
_PROMPT_THREE = "You stumbled upon a bag of a million dollars on the street and no one is around you."
_PROMPT_FOUR = "You are at a concert and the artist calls you on stage to sing one of their songs even though you have no idea what it is."


@app.on_event("startup")
def startup():
    with sqlite3.connect('mud.db') as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scenarios_table'")
        result = cursor.fetchone()
        if result:
            pass
        else:
            cursor.execute('''CREATE TABLE scenarios_table
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              scenario TEXT);''')
          
            cursor.execute("INSERT INTO scenarios_table (scenario) VALUES (?)", (_PROMPT_ONE,))
            cursor.execute("INSERT INTO scenarios_table (scenario) VALUES (?)", (_PROMPT_TWO,))
            cursor.execute("INSERT INTO scenarios_table (scenario) VALUES (?)", (_PROMPT_THREE,))
            cursor.execute("INSERT INTO scenarios_table (scenario) VALUES (?)", (_PROMPT_FOUR,))
            cursor.execute('''CREATE TABLE summary_table
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              summary TEXT);''')
            conn.commit()


@app.get("/")
async def hello_world():
  return JSONResponse(content="Hello!", status_code=200)

@app.get("/set-up")
async def set_up():
  return {"Set-Up": _SET_UP}

@app.post("/add-scenarios")
async def add_scenarios(input: str):
    with sqlite3.connect('mud.db') as conn:
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO scenarios_table (scenario) VALUES (?)", (input_scenario,))
            conn.commit()
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

        return {"message": "Scenario added successfully"}


@app.get("/view-all-scenarios")
async def view_all_scenarios():
    with sqlite3.connect('mud.db') as conn:
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT scenario FROM scenarios_table")
            rows = cursor.fetchall()
            scenarios = [row[0] for row in rows]
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

        return {"scenarios": scenarios}


@app.get("/view-scenario/{id}")
async def view_scenario(id: int):
    with sqlite3.connect('mud.db') as conn:
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT scenario FROM scenarios_table WHERE id=?", (id,))
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Prompt not found")
            scenario = row[0]
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

        return {"scenario": scenario}


@app.put("/update-scenario/{scenario_id}")
async def update_scenario(scenario_id: int, scenario_title: str):
    with sqlite3.connect('mud.db') as conn:
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE scenarios_table SET scenario = ? WHERE id = ?", (scenario_title, scenario_id))
            conn.commit()
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

        return {"message": "Scenario updated successfully"}


@app.delete("/delete-scenario/{prompt_id}")
async def delete_scenario(scenario_id: int):
    with sqlite3.connect('mud.db') as conn:
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM scenarios_table WHERE id = ?", (scenario_id,))
            conn.commit()
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

        return {"message": "Scenario deleted successfully"}
      

@app.get("/logo.png")
async def plugin_logo():
  return FileResponse('rpg_logo.png')


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest(request: Request):
  host = request.headers['host']
  with open("ai-plugin.json") as f:
    text = f.read().replace("PLUGIN_HOSTNAME", f"https://{host}")
  return JSONResponse(content=json.loads(text))

@app.get("/openapi.yaml")
async def get_openapi_yaml():
    return FileResponse("openapi.yaml")


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=5002)
