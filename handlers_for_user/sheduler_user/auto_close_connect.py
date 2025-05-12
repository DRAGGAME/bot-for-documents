async def auto_close_connect(sqlbase):
    await sqlbase.connect_close()