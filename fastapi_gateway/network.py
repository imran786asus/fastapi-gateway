import aiohttp
import async_timeout
from typing import Optional, Union
from aiohttp import JsonPayload
from starlette.datastructures import Headers
from fastapi_gateway.utils.form import CustomFormData
from fastapi_gateway.utils.response import decode_json, stream_file
from fastapi_gateway.utils.request import create_dict_if_not


async def make_request(
    url: str,
    method: str,
    headers: Union[Headers, dict],
    query: Optional[dict] = None,
    data: Union[CustomFormData, JsonPayload] = None,
    timeout: int = 60,
):
    data = create_dict_if_not(data=data)
    query = create_dict_if_not(data=query)

    async with async_timeout.timeout(delay=timeout):
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(
                method=method, url=url, params=query, data=data,allow_redirects=False
            ) as response:
                if response.status in {301, 302, 303, 307, 308}:
                    redirect_url = response.headers.get('Location')
                    return redirect_url, response.status, response.headers
                elif response.headers["Content-Type"] == "application/json":
                    response_json = await response.json()
                    decoded_json = decode_json(data=response_json)
                    return decoded_json, response.status, response.headers
                elif response.headers["Content-Type"] == "application/octet-stream":
                    file = await response.content.read()
                    return stream_file(file), response.status, response.headers
                elif "image/" in response.headers.get("Content-Type", ""):
                    file = await response.content.read()
                    return stream_file(file), response.status, response.headers
                elif "text/" in response.headers.get("Content-Type", ""):
                    text = await response.text()
                    return text, response.status, response.headers
                else:
                    raise Exception(f"Content-Type: {response.headers['Content-Type']} not supported")
