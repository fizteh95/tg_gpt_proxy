from src.domain.models import AccessCounter
from src.services.message_bus import MessageBus
from src.services.unit_of_work import AbstractUnitOfWork


class AccessManager:
    def __init__(self, uow: AbstractUnitOfWork, bus: MessageBus) -> None:
        self.uow = uow
        self.bus = bus

    async def create_access_counter_if_not_exists(self, user_id: str) -> bool:
        async with self.uow as uow:
            counter = await uow.repo.get_access_counter(user_id=user_id)
            if counter is None:
                default_access_counter = AccessCounter(
                    remain_per_day=10, remain_per_all_time=0
                )
                await uow.repo.set_access_counter(
                    user_id=user_id, access_counter=default_access_counter
                )
                return True
        return False

    async def get_access_counter(self, user_id: str) -> AccessCounter:
        async with self.uow as uow:
            counter = await uow.repo.get_access_counter(user_id=user_id)
            if counter:
                return counter
            raise Exception("Access counter not found")

    async def increase_access_counter_premium(
        self, user_id: str, count_increase: int
    ) -> None:
        async with self.uow as uow:
            counter = await uow.repo.get_access_counter(user_id=user_id)
            if counter is None:
                raise Exception("Access counter not found")
            counter.remain_per_all_time += count_increase
            await uow.repo.set_access_counter(user_id=user_id, access_counter=counter)

    async def increase_access_counter_usual(
        self, user_id: str, count_increase: int
    ) -> None:
        async with self.uow as uow:
            counter = await uow.repo.get_access_counter(user_id=user_id)
            if counter is None:
                raise Exception("Access counter not found")
            counter.remain_per_day += count_increase
            await uow.repo.set_access_counter(user_id=user_id, access_counter=counter)

    async def decrement_access_counter_premium(
        self, user_id: str, count_decrease: int = 1
    ) -> bool:
        async with self.uow as uow:
            counter = await uow.repo.get_access_counter(user_id=user_id)
            if counter is None:
                raise Exception("Access counter not found")
            counter.remain_per_all_time -= count_decrease
            await uow.repo.set_access_counter(user_id=user_id, access_counter=counter)
        if counter.remain_per_all_time <= 0:
            return True
        return False

    async def decrement_access_counter_usual(
        self, user_id: str, count_decrease: int = 1
    ) -> bool:
        async with self.uow as uow:
            counter = await uow.repo.get_access_counter(user_id=user_id)
            if counter is None:
                raise Exception("Access counter not found")
            counter.remain_per_day -= count_decrease
            await uow.repo.set_access_counter(user_id=user_id, access_counter=counter)
        if counter.remain_per_day <= 0:
            return True
        return False

    async def refresh_access_counter_usual(self, count_level: int) -> None:
        async with self.uow as uow:
            await uow.repo.set_access_counter_usual_for_everybody(
                count_level=count_level
            )
